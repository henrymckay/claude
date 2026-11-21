# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Start an unattended Claude Code run from a prompt file, isolated, bounded and resumed.

The run gets only what the project needs: house plugins and the MCP servers named, no
claude.ai connectors, the sandbox on, writes confined to the project and a scratch folder,
the secrets the standing grant names and no other environment. The launcher resumes the
same session after a drop until the run ends with its marker, stops it at the spend or turn
limit, and reports finished, blocked, limit or failed.
"""

import argparse
import collections.abc
import dataclasses
import datetime
import decimal
import json
import os
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
import threading
import time
import typing
import uuid

_SKILLS = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_SKILLS / "choose-model" / "scripts"))
sys.path.insert(0, str(_SKILLS / "secure-project" / "scripts"))

import costs
import grant as grant_

_CENT: typing.Final = decimal.Decimal("0.01")
_MARKER: typing.Final = "LAUNCHER:"
_EXIT: typing.Final = {"blocked": 3, "failed": 5, "finished": 0, "limit": 4}
_DOCS_DOMAINS: typing.Final = (
    "code.claude.com",
    "developer.mozilla.org",
    "developers.cloudflare.com",
    "docs.astral.sh",
    "docs.github.com",
    "docs.ntfy.sh",
    "docs.pola.rs",
    "docs.python.org",
    "duckdb.org",
    "echarts.apache.org",
    "fastapi.tiangolo.com",
    "motherduck.com",
    "playwright.dev",
    "pypi.org",
    "react.dev",
    "tailwindcss.com",
    "tanstack.com",
    "typescriptlang.org",
    "ui.shadcn.com",
    "vite.dev",
    "zod.dev",
)
_PACKAGE_DOMAINS: typing.Final = (
    "files.pythonhosted.org",
    "pypi.org",
    "registry.npmjs.org",
)
_SECRET_READS: typing.Final = (
    "Read(**/.env)",
    "Read(**/.env.*)",
    "Read(**/.envrc)",
    "Read(**/*.pem)",
    "Read(**/*.key)",
    "Read(~/.aws/**)",
    "Read(~/.config/gh/**)",
    "Read(~/.docker/**)",
    "Read(~/.kube/**)",
    "Read(~/.netrc)",
    "Read(~/.ssh/**)",
)
_TOOLCHAIN_SECRETS: typing.Final = (
    "~/.cargo/credentials",
    "~/.cargo/credentials.toml",
    "~/.config/git/credentials",
    "~/.local/share/keyrings",
    "~/.local/share/uv/credentials",
)
_TOOLCHAIN_READS: typing.Final = (
    "~/.bun",
    "~/.cargo",
    "~/.config/git",
    "~/.deno",
    "~/.gitconfig",
    "~/.local",
    "~/.nvm",
    "~/.pyenv",
    "~/.rustup",
    "~/.volta",
)
_PASSED_ENVIRONMENT: typing.Final = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_BASE_URL",
    "CLAUDE_CODE_OAUTH_TOKEN",
    "HOME",
    "LANG",
    "LC_ALL",
    "LOGNAME",
    "PATH",
    "SHELL",
    "TERM",
    "USER",
)
_CLAUDE_CREDENTIALS: typing.Final = (
    "ANTHROPIC_API_KEY",
    "CLAUDE_CODE_OAUTH_TOKEN",
)
_TOOLS: typing.Final = (
    "Bash",
    "Edit",
    "Glob",
    "Grep",
    "NotebookEdit",
    "Read",
    "Skill",
    "Task",
    "TaskStop",
    "TodoWrite",
    "ToolSearch",
    "WebFetch",
    "WebSearch",
    "Write",
)
_FIRST_NOTE: typing.Final = f"""

---
This run is unattended: a launcher started it and nobody is watching. When the whole
task is done, end your final message with the line `{_MARKER} finished`. If you cannot
go on without the owner, end it with `{_MARKER} blocked: <the one thing you need>`. A
final message with neither line is taken as an interruption, and the session resumed.
"""
_RESUME_NOTE: typing.Final = f"""The launcher resumed this session after {{why}}. Check
the repository's state, carry on from where the work stopped, and end as instructed:
`{_MARKER} finished`, or `{_MARKER} blocked: <the one thing you need>`."""


class LaunchError(Exception):
    """A launch that cannot start: no limit, an unreadable prompt or grant."""


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Limits:
    """The spend and turn limits a run stops at."""

    budget_usd: decimal.Decimal
    max_turns: int | None


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Layout:
    """Where a run's files live: the launcher's own folder and the run's scratch folder."""

    root: pathlib.Path
    work: pathlib.Path

    @property
    def grant(self) -> pathlib.Path:
        """Return the grant snapshot the guard hook reads."""
        return self.root / "grant.json"

    @property
    def log(self) -> pathlib.Path:
        """Return the stream of every invocation's output."""
        return self.root / "run.jsonl"

    @property
    def mcp(self) -> pathlib.Path:
        """Return the MCP configuration the run is limited to."""
        return self.root / "mcp.json"

    @property
    def profile(self) -> pathlib.Path:
        """Return the settings file the run starts under."""
        return self.root / "profile.json"

    @property
    def status(self) -> pathlib.Path:
        """Return the outcome record."""
        return self.root / "status.json"


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Outcome:
    """How one invocation of ``claude`` ended."""

    cost_usd: decimal.Decimal
    killed: str
    subtype: str
    text: str
    turns: int


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Report:
    """How the whole run ended."""

    detail: str
    invocations: int
    session: str
    spent_usd: decimal.Decimal
    state: typing.Literal["blocked", "failed", "finished", "limit"]
    turns: int

    def line(self) -> str:
        """Return the one-line report a person or a message reads."""
        return (
            f"{self.state}: {self.detail} (session {self.session}, "
            f"${self.spent_usd:.2f}, {self.turns} turns, {self.invocations} invocations)"
        )


def _choose_limits(
    *, budget: float | None, grant: grant_.Grant | None, turns: int | None
) -> Limits:
    """Return the run's limits: the lower of the command line's and the grant's.

    :param budget: The spend limit in dollars from the command line.
    :param grant: The standing grant, if any.
    :param turns: The turn limit from the command line.
    :returns: The limits.
    :raises LaunchError: If neither sets a spend limit.
    """
    budgets = [
        value for value in (budget, grant and grant.budget_usd) if value is not None
    ]
    if not budgets:
        raise LaunchError(
            "no spend limit: pass --budget-usd or set run.budget_usd in the grant"
        )
    caps = [value for value in (turns, grant and grant.max_turns) if value is not None]
    return Limits(
        budget_usd=decimal.Decimal(str(min(budgets))),
        max_turns=min(caps) if caps else None,
    )


def _find_house_plugins(claude: str) -> list[pathlib.Path]:
    """Return the folders of this plugin's marketplace siblings, to load with --plugin-dir.

    From a marketplace checkout, that is every plugin folder beside this one; from an
    install, every enabled plugin of the same marketplace that ``claude plugin list``
    reports.

    :param claude: The ``claude`` executable.
    :returns: The plugin folders.
    """
    plugin = _SKILLS.parent
    if (plugin.parent.parent / ".claude-plugin" / "marketplace.json").exists():
        return sorted(
            folder
            for folder in plugin.parent.iterdir()
            if (folder / ".claude-plugin" / "plugin.json").exists()
        )
    listed = subprocess.run(
        [claude, "plugin", "list", "--json"],
        capture_output=True,
        check=True,
        text=True,
        timeout=60,
    )
    own = next(
        (
            entry["id"]
            for entry in json.loads(listed.stdout)
            if pathlib.Path(entry["installPath"]) == plugin
        ),
        "",
    )
    marketplace = own.partition("@")[2]
    return [
        pathlib.Path(entry["installPath"])
        for entry in json.loads(listed.stdout)
        if marketplace
        and entry["id"].endswith(f"@{marketplace}")
        and entry.get("enabled")
    ]


def build_environment(
    *,
    grant: grant_.Grant | None,
    layout: Layout,
    source: collections.abc.Mapping[str, str],
) -> dict[str, str]:
    """Return the run's environment: a few basics, the grant's secrets, the launcher's own.

    :param grant: The standing grant, whose ``secrets`` name what may pass.
    :param layout: The run's folders.
    :param source: The launcher's own environment.
    :returns: The environment ``claude`` starts with.
    """
    named = (*_PASSED_ENVIRONMENT, *(grant.secrets if grant else ()))
    passed = {name: source[name] for name in named if name in source}
    return (
        passed
        | {
            "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS": "0",
            "CLAUDE_GUARD": "deny",
            "ENABLE_CLAUDEAI_MCP_SERVERS": "false",
            "TMPDIR": str(layout.work),
            "UV_CACHE_DIR": str(layout.work / "uv-cache"),
            "npm_config_cache": str(layout.work / "npm-cache"),
        }
        | ({"CLAUDE_GRANT_FILE": str(layout.grant)} if grant else {})
    )


def build_profile(
    *,
    grant: grant_.Grant | None,
    layout: Layout,
    mode: str,
    plugins: collections.abc.Sequence[pathlib.Path],
    project: pathlib.Path,
    reads: collections.abc.Sequence[str],
) -> dict[str, typing.Any]:
    """Return the settings a run starts under.

    :param grant: The standing grant, whose ``network`` and ``web`` widen the defaults.
    :param layout: The run's folders.
    :param mode: The permission mode.
    :param plugins: The plugin folders loaded, which the sandbox lets commands read.
    :param project: The project folder.
    :param reads: More folders sandboxed commands may read.
    :returns: The settings, as ``--settings`` takes them.
    """
    web = grant.web if grant else "docs"
    fetch = {
        "docs": [f"WebFetch(domain:{domain})" for domain in _DOCS_DOMAINS],
        "open": ["WebFetch"],
        "off": [],
    }[web]
    transcripts = (
        pathlib.Path.home()
        / ".claude"
        / "projects"
        / re.sub(r"[^A-Za-z0-9]", "-", str(project))
    )
    return {
        "disableClaudeAiConnectors": True,
        "enableAllProjectMcpServers": False,
        "permissions": {
            "allow": [tool for tool in _TOOLS if tool != "WebFetch"] + fetch,
            "defaultMode": mode,
            "deny": [*_SECRET_READS, *(["WebFetch"] if web == "off" else [])],
            "disableBypassPermissionsMode": "disable",
        },
        "sandbox": {
            "allowUnsandboxedCommands": False,
            "autoAllowBashIfSandboxed": True,
            "credentials": {
                "envVars": [
                    {"mode": "deny", "name": name} for name in _CLAUDE_CREDENTIALS
                ]
            },
            "enabled": True,
            "failIfUnavailable": True,
            "filesystem": {
                "allowRead": [
                    str(project),
                    str(layout.work),
                    str(transcripts),
                    *(str(plugin) for plugin in plugins),
                    *_TOOLCHAIN_READS,
                    *reads,
                ],
                "allowWrite": [str(layout.work)],
                "denyRead": ["~/", *_TOOLCHAIN_SECRETS],
            },
            "network": {
                "allowedDomains": sorted(
                    {*_PACKAGE_DOMAINS, *(grant.network if grant else ())}
                )
            },
        },
    }


def build_command(
    *,
    claude: str,
    layout: Layout,
    limits_left: Limits,
    model: str,
    plugins: collections.abc.Sequence[pathlib.Path],
    prompt: str,
    resume: bool,
    session: str,
) -> list[str]:
    """Return one invocation of ``claude`` under the profile.

    :param claude: The ``claude`` executable.
    :param layout: The run's folders.
    :param limits_left: What is left of the spend and turn limits.
    :param model: The session's model.
    :param plugins: The plugin folders to load.
    :param prompt: The prompt for this invocation.
    :param resume: Whether to resume the session rather than start it.
    :param session: The session's id.
    :returns: The command's words.
    """
    command = [
        claude,
        "-p",
        "--restricted",
        "--tools", ",".join(_TOOLS),
        "--strict-mcp-config",
        "--mcp-config", str(layout.mcp),
        "--settings", str(layout.profile),
        "--permission-prompts", "none",
        "--add-dir", str(layout.work),
        "--model", model,
        "--output-format", "stream-json",
        "--verbose",
        "--max-budget-usd", str(max(limits_left.budget_usd.quantize(_CENT, rounding=decimal.ROUND_CEILING), _CENT)),
    ]  # fmt: skip
    if limits_left.max_turns is not None:
        command += ["--max-turns", str(limits_left.max_turns)]
    for plugin in plugins:
        command += ["--plugin-dir", str(plugin)]
    command += ["--resume", session] if resume else ["--session-id", session]
    return [*command, prompt]


def measure(session: str) -> tuple[decimal.Decimal, int]:
    """Return a session's list-price spend and turns so far, read from its transcripts.

    A turn is one response of the session's own model loop, as ``--max-turns`` counts
    them, subagents' responses not counted; the result's ``num_turns`` counts tool calls
    instead, so forty calls made in parallel in one response read as 41 there and 1 here.
    The launcher passes ``--max-turns`` too, but it resets on each resume.

    :param session: The session's id.
    :returns: The dollars, subagents included, and the turns; zero for both before the
        transcript exists.
    """
    found = sorted(
        (pathlib.Path.home() / ".claude" / "projects").glob(f"*/{session}.jsonl")
    )
    if not found:
        return decimal.Decimal(0), 0
    rows = costs.total_session(found[0])
    spent = sum(
        (decimal.Decimal(row["dollars"]) for row in rows if row["dollars"]),
        decimal.Decimal(0),
    )
    responses: set[str] = set()
    with found[0].open(encoding="utf-8") as lines:
        for line in lines:
            try:
                record = json.loads(line)
            except ValueError:
                continue
            message = record.get("message") if isinstance(record, dict) else None
            if record.get("type") == "assistant" and isinstance(message, dict):
                responses.add(str(message.get("id") or record.get("uuid")))
    return spent, len(responses)


def _read_outcome(lines: collections.abc.Iterable[str], *, killed: str) -> Outcome:
    """Return how an invocation ended, from its stream-json output.

    :param lines: The invocation's standard output.
    :param killed: Which limit the launcher stopped it at, empty where it did not.
    :returns: The outcome; ``subtype`` is empty where no result arrived.
    """
    result: dict[str, typing.Any] = {}
    for line in lines:
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if isinstance(record, dict) and record.get("type") == "result":
            result = record
    return Outcome(
        cost_usd=decimal.Decimal(str(result.get("total_cost_usd") or 0)),
        killed=killed,
        subtype=str(result.get("subtype", "")),
        text=str(result.get("result", "")),
        turns=int(result.get("num_turns") or 0),
    )


def _invoke(
    command: list[str],
    *,
    environment: dict[str, str],
    layout: Layout,
    limits: Limits,
    poll_seconds: float,
    project: pathlib.Path,
    session: str,
) -> Outcome:
    """Run one invocation, stopping it once the transcript shows a limit reached.

    :param command: The invocation.
    :param limits: The whole run's spend and turn limits.
    :param environment: Its environment.
    :param layout: The run's folders, whose log receives its output.
    :param poll_seconds: How often to read the transcript's spend.
    :param project: The folder it runs in.
    :param session: The session's id.
    :returns: How it ended.
    """
    stopped: list[str] = []
    with layout.log.open("a", encoding="utf-8") as log:
        log.write(
            json.dumps(
                {"launcher": "invoke", "at": _now(), "resume": "--resume" in command}
            )
            + "\n"
        )
        log.flush()
        offset = log.tell()
        process = subprocess.Popen(
            command,
            cwd=project,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
        )

        def watch() -> None:
            while process.poll() is None:
                spent, turns = measure(session)
                if spent >= limits.budget_usd:
                    stopped.append("spend")
                elif limits.max_turns is not None and turns >= limits.max_turns:
                    stopped.append("turns")
                if stopped:
                    process.terminate()
                    try:
                        process.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    return
                time.sleep(poll_seconds)

        watcher = threading.Thread(target=watch, daemon=True)
        watcher.start()
        process.wait()
        watcher.join(timeout=5)
    with layout.log.open(encoding="utf-8") as log:
        log.seek(offset)
        return _read_outcome(log, killed=stopped[0] if stopped else "")


def _now() -> str:
    """Return the time now in UTC, for the log."""
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def _classify(outcome: Outcome) -> tuple[str, str]:
    """Return what an invocation's end means for the run, and why.

    :param outcome: How the invocation ended.
    :returns: ``finished``, ``blocked`` or ``limit`` with the detail, or ``resume``
        with the reason to resume.
    """
    if outcome.killed == "spend" or outcome.subtype == "error_max_budget_usd":
        return "limit", "the spend limit was reached"
    if outcome.killed == "turns" or outcome.subtype == "error_max_turns":
        return "limit", "the turn limit was reached"
    last = next(
        (
            line.strip()
            for line in reversed(outcome.text.splitlines())
            if line.strip().startswith(_MARKER)
        ),
        "",
    )
    if outcome.subtype == "success" and last.startswith(f"{_MARKER} finished"):
        return "finished", "the run ended with its marker"
    if outcome.subtype == "success" and last.startswith(f"{_MARKER} blocked"):
        return "blocked", last.removeprefix(f"{_MARKER} blocked").lstrip(" :—-")
    if outcome.subtype == "success":
        return "resume", "a final message with no end marker"
    return "resume", f"an interruption ({outcome.subtype or 'no result'})"


def run(
    *,
    claude: str,
    environment: dict[str, str],
    layout: Layout,
    limits: Limits,
    max_resumes: int,
    model: str,
    plugins: list[pathlib.Path],
    poll_seconds: float,
    project: pathlib.Path,
    prompt: str,
    retry_wait: float,
) -> Report:
    """Run a session to its end marker, resuming after drops, within the limits.

    :param claude: The ``claude`` executable.
    :param environment: The run's environment.
    :param layout: The run's folders.
    :param limits: The spend and turn limits for the whole run.
    :param max_resumes: How many resumes to try before giving up.
    :param model: The session's model.
    :param plugins: The plugin folders to load.
    :param poll_seconds: How often to read the spend while an invocation runs.
    :param project: The folder it runs in.
    :param prompt: The task.
    :param retry_wait: Seconds to wait before the first resume after a drop, doubled
        after each drop up to fifteen minutes.
    :returns: How it ended.
    """
    session = str(uuid.uuid4())
    print(f"launch: session {session}", file=sys.stderr, flush=True)
    turns = 0
    invocations = 0
    drops = 0
    why = ""
    while True:
        spent, measured = measure(session)
        turns = max(turns, measured)
        report = _reporter(
            session=session, spent=spent, turns=turns, invocations=invocations
        )
        if spent >= limits.budget_usd:
            return report("limit", "the spend limit was reached")
        if limits.max_turns is not None and turns >= limits.max_turns:
            return report("limit", "the turn limit was reached")
        if invocations > max_resumes:
            return report("failed", f"gave up after {max_resumes} resumes; last: {why}")
        left = Limits(
            budget_usd=limits.budget_usd - spent,
            max_turns=None if limits.max_turns is None else limits.max_turns - turns,
        )
        command = build_command(
            claude=claude,
            layout=layout,
            limits_left=left,
            model=model,
            plugins=plugins,
            prompt=prompt + _FIRST_NOTE
            if invocations == 0
            else _RESUME_NOTE.format(why=why),
            resume=invocations > 0,
            session=session,
        )
        outcome = _invoke(
            command,
            environment=environment,
            layout=layout,
            limits=limits,
            poll_seconds=poll_seconds,
            project=project,
            session=session,
        )
        invocations += 1
        state, detail = _classify(outcome)
        if state != "resume":
            final_spent, measured = measure(session)
            spent = max(final_spent, spent + outcome.cost_usd)
            turns = max(measured, turns)
            return _reporter(
                session=session, spent=spent, turns=turns, invocations=invocations
            )(state, detail)
        why = detail
        if outcome.subtype != "success":
            time.sleep(min(retry_wait * 2**drops, 900))
            drops += 1


def _reporter(
    *, invocations: int, session: str, spent: decimal.Decimal, turns: int
) -> collections.abc.Callable[[str, str], Report]:
    """Return a function that builds the run's report from its state and detail.

    :param invocations: How many times ``claude`` ran.
    :param session: The session's id.
    :param spent: The dollars spent.
    :param turns: The turns taken.
    :returns: The builder.
    """

    def build(state: str, detail: str) -> Report:
        return Report(
            detail=detail,
            invocations=invocations,
            session=session,
            spent_usd=spent,
            state=typing.cast(
                typing.Literal["blocked", "failed", "finished", "limit"], state
            ),
            turns=turns,
        )

    return build


def _prepare(
    *,
    grant_path: pathlib.Path | None,
    mcp_config: pathlib.Path | None,
    project: pathlib.Path,
    runs: pathlib.Path,
) -> tuple[Layout, grant_.Grant | None]:
    """Return the run's folders, made, with the grant snapshot and MCP configuration in place.

    :param grant_path: The grant to snapshot, if any.
    :param mcp_config: The MCP servers the project needs, if any.
    :param project: The project folder.
    :param runs: The folder that holds every run's own folder, outside any temp folder.
    :returns: The layout and the grant read from the snapshot.
    :raises LaunchError: If the grant is malformed or expired.
    """
    stamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
    root = runs / f"{project.name}-{stamp}-{uuid.uuid4().hex[:6]}"
    layout = Layout(root=root, work=root / "work")
    layout.work.mkdir(parents=True, mode=0o700)
    root.chmod(0o700)
    grant = None
    if grant_path is not None:
        try:
            grant = grant_.read_grant(grant_path)
        except grant_.GrantError as failure:
            raise LaunchError(str(failure)) from failure
        shutil.copyfile(grant_path, layout.grant)
        layout.grant.chmod(0o400)
        grant = grant._replace(path=layout.grant)
    servers = (
        json.loads(mcp_config.read_text(encoding="utf-8"))
        if mcp_config
        else {"mcpServers": {}}
    )
    layout.mcp.write_text(json.dumps(servers), encoding="utf-8")
    return layout, grant


def _prepare_repository(project: pathlib.Path, *, commit_as: str) -> None:
    """Make the project a git repository with its identity set, before the sandbox starts.

    The sandbox denies writes to ``.git/config`` and ``.git/hooks``, so a run cannot
    ``git init``, set its identity or add a remote itself; commits, which write only
    objects, refs and the index, still work.

    :param project: The project folder.
    :param commit_as: ``Name <email>`` to commit as, empty to leave the identity alone.
    :raises LaunchError: If git fails.
    """
    commands: list[list[str]] = []
    if not (project / ".git").exists():
        commands.append(["git", "init", "-q", "-b", "main"])
    if commit_as:
        name, _, email = commit_as.partition("<")
        commands += [
            ["git", "config", "user.name", name.strip()],
            ["git", "config", "user.email", email.rstrip(">").strip()],
        ]
    for command in commands:
        done = subprocess.run(
            command, capture_output=True, check=False, cwd=project, text=True
        )
        if done.returncode != 0:
            raise LaunchError(f"{shlex.join(command)} failed: {done.stderr.strip()}")


def _notify(command: str, line: str) -> None:
    """Hand the report line to the owner's message command, if one was given.

    :param command: The command, split as a shell would, the line appended as its last
        argument; never run through a shell.
    :param line: The report line.
    """
    if not command:
        return
    try:
        subprocess.run([*shlex.split(command), line], check=False, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as failure:
        print(f"notify failed: {failure}", file=sys.stderr)


def main() -> None:
    """Parse the command line, launch the run and report how it ended."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt", type=pathlib.Path, help="the prompt file")
    parser.add_argument(
        "--allow-read",
        action="append",
        default=[],
        help="another folder sandboxed commands may read",
    )
    parser.add_argument(
        "--budget-usd",
        type=float,
        help="stop at this list-price spend; the grant's run.budget_usd caps it",
    )
    parser.add_argument("--claude", default="claude", help="the claude executable")
    parser.add_argument(
        "--commit-as",
        default="",
        help="'Name <email>' set as the repository's identity before the run",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="write the profile and print the command, run nothing",
    )
    parser.add_argument(
        "--grant",
        type=pathlib.Path,
        help="the standing grant; default: the project's grant.json",
    )
    parser.add_argument("--max-resumes", type=int, default=5)
    parser.add_argument(
        "--max-turns",
        type=int,
        help="stop after this many turns; the grant's run.max_turns caps it",
    )
    parser.add_argument(
        "--mcp-config",
        type=pathlib.Path,
        help="the MCP servers the project needs; default: none",
    )
    parser.add_argument(
        "--model",
        default="opus",
        help="the session's model; stages hand work to their own",
    )
    parser.add_argument(
        "--notify",
        default="",
        help="a command given the report line as its last argument",
    )
    parser.add_argument(
        "--permission-mode", default="dontAsk", choices=("auto", "dontAsk")
    )
    parser.add_argument(
        "--plugin-dir",
        action="append",
        type=pathlib.Path,
        default=[],
        help="a plugin to load; default: this marketplace's",
    )
    parser.add_argument("--poll-seconds", type=float, default=20.0)
    parser.add_argument("--project", type=pathlib.Path, default=pathlib.Path.cwd())
    parser.add_argument(
        "--retry-wait",
        type=float,
        default=60.0,
        help="seconds before the first resume after a drop",
    )
    parser.add_argument(
        "--runs-dir",
        type=pathlib.Path,
        default=pathlib.Path.home() / ".cache" / "claude-runs",
    )
    arguments = parser.parse_args()
    project = arguments.project.resolve()
    try:
        prompt = arguments.prompt.read_text(encoding="utf-8")
        grant_path = arguments.grant or grant_.find_grant(project)
        layout, grant = _prepare(
            grant_path=grant_path,
            mcp_config=arguments.mcp_config,
            project=project,
            runs=arguments.runs_dir,
        )
        limits = _choose_limits(
            budget=arguments.budget_usd, grant=grant, turns=arguments.max_turns
        )
        if not arguments.dry_run:
            _prepare_repository(project, commit_as=arguments.commit_as)
    except (LaunchError, OSError) as failure:
        raise SystemExit(f"launch: {failure}") from failure
    plugins = arguments.plugin_dir or _find_house_plugins(arguments.claude)
    profile = build_profile(
        grant=grant,
        layout=layout,
        mode=arguments.permission_mode,
        plugins=plugins,
        project=project,
        reads=arguments.allow_read,
    )
    layout.profile.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    layout.profile.chmod(0o400)
    environment = build_environment(grant=grant, layout=layout, source=os.environ)
    print(f"launch: run folder {layout.root}", file=sys.stderr)
    if arguments.dry_run:
        command = build_command(
            claude=arguments.claude, layout=layout, limits_left=limits, model=arguments.model,
            plugins=plugins, prompt="<prompt>", resume=False, session="<session>",
        )  # fmt: skip
        print(shlex.join(command))
        print("environment:", " ".join(sorted(environment)))
        return
    report = run(
        claude=arguments.claude,
        environment=environment,
        layout=layout,
        limits=limits,
        max_resumes=arguments.max_resumes,
        model=arguments.model,
        plugins=plugins,
        poll_seconds=arguments.poll_seconds,
        project=project,
        prompt=prompt,
        retry_wait=arguments.retry_wait,
    )
    record = dataclasses.asdict(report) | {
        "spent_usd": f"{report.spent_usd:.2f}",
        "ended": _now(),
    }
    layout.status.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(report.line())
    _notify(arguments.notify, report.line())
    raise SystemExit(_EXIT[report.state])


if __name__ == "__main__":
    main()
