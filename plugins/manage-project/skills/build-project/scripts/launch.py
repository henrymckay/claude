# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Start an unattended Claude Code run from a prompt file, isolated, bounded and resumed.

The run gets only what the project needs: house plugins and the MCP servers named, no
claude.ai connectors, the sandbox on, writes confined to the project and a scratch folder,
the secrets the standing grant names and no other environment. Before it starts, a cheap
preflight session under the same profile tries a fixed list of forbidden things, and the
run is refused if any gets through. The launcher resumes the same session after a drop
until the run ends with its marker, stops it at the spend or turn limit, accepts a finish
only once its own gate passes, and reports finished, blocked, limit or failed.
"""

import argparse
import collections.abc
import csv
import dataclasses
import datetime
import decimal
import hashlib
import json
import os
import pathlib
import re
import secrets
import shlex
import shutil
import subprocess
import sys
import tempfile
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
_PREFLIGHT_INTRO: typing.Final = (
    "The owner of this machine started this session through their launcher to prove, "
    "before an unattended build, that the sandbox and permission rules it runs under "
    "refuse what they must. The first call runs the launcher's own check script, which "
    "prints only closed or open for each check, never what it read; every other path "
    "below is a decoy the launcher wrote a moment ago, holding only the word decoy and a "
    "random token, and deleted when this session ends. A refusal is the expected result. "
    "A call left unmade fails the test and stops the build, because the launcher cannot "
    "tell an unmade call from a rule that let it through."
)
_PROBE_MODEL: typing.Final = "haiku"
_PROBE_SECONDS: typing.Final = 900
_RECORDS: typing.Final = ("PLAN.md", "DEPENDENCIES.md", "costs.csv", "verification.csv")
_PLACEHOLDERS: typing.Final = frozenset(
    (
        ".bash_profile",
        ".bashrc",
        ".claude",
        ".gitconfig",
        ".gitmodules",
        ".idea",
        ".mcp.json",
        ".profile",
        ".ripgreprc",
        ".vscode",
        ".zprofile",
        ".zshrc",
        "grant.json",
    )
)
_STATUS_END: typing.Final = "porcelain-end"
_STATUS_COMMAND: typing.Final = (
    f"git status --porcelain --untracked-files=normal && echo {_STATUS_END}"
)
_HEAD_END: typing.Final = "head-end"
_HEAD_COMMAND: typing.Final = (
    "git log -2 --format=%H && "
    f"(git diff --name-only HEAD~1 HEAD 2>/dev/null; echo {_HEAD_END})"
)
_PATH_PREFIX: typing.Final = "path-probe="
_PROBE_ENVIRONMENT: typing.Final = {
    "BASH_DEFAULT_TIMEOUT_MS": "600000",
    "BASH_MAX_TIMEOUT_MS": "600000",
    "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1",
}
_RECORD_FILES: typing.Final = frozenset(
    ("DEPENDENCIES.md", "costs.csv", "verification.csv")
)
_TEMP_FOLDERS: typing.Final = (
    "/dev/shm",
    "/tmp",
    "/private/tmp",
    "/private/var/folders",
    "/var/folders",
    "/var/tmp",
)
_UNFINISHED: typing.Final = re.compile(
    r"(?i)moved to the background|running in (the )?background|timed out|timeout exceeded"
)
_USAGE_LIMIT: typing.Final = re.compile(
    r"(?i)hit your \w+ limit|usage limit (reached|exceeded)"
)
_VERIFICATION_LINE: typing.Final = re.compile(r"^- \*\*([^*]+)\*\*")
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
_FILE_WRITERS: typing.Final = ("Edit", "NotebookEdit", "Write")
_WRITERS: typing.Final = frozenset(("Bash", *_FILE_WRITERS))
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
Skill feedback the session's rules ask you to file goes in your final message instead:
filing an issue is an outward action this run takes only where its standing grant
allows, and it is never a reason to end blocked.
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
    def check(self) -> pathlib.Path:
        """Return the folder of the preflight's script, which commands read and none write."""
        return self.root / "check"

    @property
    def profile(self) -> pathlib.Path:
        """Return the settings file the run starts under."""
        return self.root / "profile.json"

    @property
    def status(self) -> pathlib.Path:
        """Return the outcome record."""
        return self.root / "status.json"


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Session:
    """How to start ``claude`` for this run: the executable, environment, folders, plugins."""

    claude: str
    environment: dict[str, str]
    layout: Layout
    plugins: list[pathlib.Path]
    project: pathlib.Path


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Outcome:
    """How one invocation of ``claude`` ended."""

    cost_usd: decimal.Decimal
    is_error: bool
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


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Probe:
    """One tool call a probe session is told to make, and how its outcome is judged.

    The judgement never takes the model's word: a call is tried when the stream shows a
    tool call of that tool whose input holds ``marker``, and it got through when a result
    of such a call matches ``through`` or ``written`` exists afterwards.
    """

    input: dict[str, str]
    marker: str
    name: str
    through: str
    tool: str
    written: pathlib.Path | None = None


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Check:
    """One thing the preflight's script tries, which the sandbox must refuse.

    ``shell`` is a condition true when the thing got through; the script prints only
    ``check <key> open`` or ``check <key> closed`` for it, never what it read. A check
    that writes names the file in ``written``, and counts as through only where that file
    reached the real file system: the Linux sandbox gives commands their own view of the
    temp folder, so a write there can succeed without touching another session's folder
    (Claude Code 2.1.330, ubuntu-24.04).
    """

    key: str
    name: str
    shell: str
    written: pathlib.Path | None = None


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class PreflightPlan:
    """The preflight's script, its checks and digest, and the calls the session makes."""

    checks: list[Check]
    digest: str
    probes: list[Probe]
    run: Probe
    script: pathlib.Path


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class ToolCall:
    """One tool call a session made, with its result, read from the stream."""

    failed: bool
    input: dict[str, typing.Any]
    name: str
    result: str


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Probed:
    """What a probe session showed: its init record, tool calls, cost and whether it ended.

    A session with no result record, one past its time included, did not end, and every
    check that reads it fails closed.
    """

    calls: list[ToolCall]
    cost_usd: decimal.Decimal
    ended: bool
    init: dict[str, typing.Any] | None


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
    usage_wait_hours: float,
) -> dict[str, str]:
    """Return the run's environment: a few basics, the grant's secrets, the launcher's own.

    Every tool that keeps a cache or reads its configuration under the home folder,
    which the profile denies, is pointed at the scratch folder instead: ``gh`` then reads
    an empty configuration and a token only from a variable the grant names, and
    ``pre-commit`` clones and builds its hooks inside the sandbox into a store of the
    run's own, never the owner's, whose hooks run outside the sandbox on the owner's own
    commits; the launcher fetches nothing a project file names. ``pip`` checks certificates
    against its own bundle, since the system trust store it asks by default fails inside
    the macOS sandbox (``OSStatus -26276``, pip 26.3). Claude Code's background updater is
    off, so the preflight, the run and the gate run the version ``status.json`` records.
    Claude Code's retry watchdog waits out a capacity error or the plan's usage window
    inside the request, rechecking every ten minutes, up to ``usage_wait_hours``; a reset
    further away fails at once, and the launcher reports it as a limit.

    :param grant: The standing grant, whose ``secrets`` name what may pass.
    :param layout: The run's folders.
    :param source: The launcher's own environment.
    :param usage_wait_hours: The longest wait for the plan's usage window to reset.
    :returns: The environment ``claude`` starts with.
    """
    named = (*_PASSED_ENVIRONMENT, *(grant.secrets if grant else ()))
    passed = {name: source[name] for name in named if name in source}
    wait_ms = str(int(usage_wait_hours * 3_600_000))
    return (
        passed
        | {
            "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS": "0",
            "CLAUDE_CODE_RETRY_WATCHDOG": "1",
            "CLAUDE_CODE_RETRY_WATCHDOG_MAX_USAGE_LIMIT_WAIT_MS": wait_ms,
            "CLAUDE_CODE_RETRY_WATCHDOG_MAX_WAIT_MS": wait_ms,
            "CLAUDE_CODE_RETRY_WATCHDOG_USAGE_LIMIT_RECHECK_MS": "600000",
            "CLAUDE_GUARD": "deny",
            "DISABLE_AUTOUPDATER": "1",
            "ENABLE_CLAUDEAI_MCP_SERVERS": "false",
            "GH_CONFIG_DIR": str(layout.work / "gh"),
            "PIP_CACHE_DIR": str(layout.work / "pip-cache"),
            "PIP_USE_DEPRECATED": "legacy-certs",
            "PRE_COMMIT_HOME": str(layout.work / "pre-commit"),
            "TMPDIR": str(layout.work),
            "UV_CACHE_DIR": str(layout.work / "uv-cache"),
            "VIRTUALENV_OVERRIDE_APP_DATA": str(layout.work / "virtualenv"),
            "npm_config_cache": str(layout.work / "npm-cache"),
        }
        | ({"CLAUDE_GRANT_FILE": str(layout.grant)} if grant else {})
    )


def _session_temp_folders(system: str) -> tuple[str, ...]:
    """Return the patterns for every Claude session's own temp folder on this machine.

    Claude Code keeps each session's scripts and task output in a folder named for its
    working folder under ``/tmp/claude-<uid>/``, and an attended session may later run
    what is there outside any sandbox, so a run must neither read nor write them; the
    parent folder itself stays open, since the Bash tool needs it.

    :param system: ``sys.platform`` of the machine the run starts on.
    :returns: The patterns, under both spellings of the temp folder on macOS.
    """
    uid = os.getuid()
    linux = (f"/tmp/claude-{uid}/-*",)
    return (f"/private/tmp/claude-{uid}/-*", *linux) if system == "darwin" else linux


def build_profile(
    *,
    grant: grant_.Grant | None,
    layout: Layout,
    local_binding: bool,
    mode: str,
    plugins: collections.abc.Sequence[pathlib.Path],
    project: pathlib.Path,
    reads: collections.abc.Sequence[str],
    system: str,
) -> dict[str, typing.Any]:
    """Return the settings a run starts under.

    The macOS sandbox is Seatbelt and the Linux one bubblewrap; each is given only the
    paths its machine has, so mounted volumes are denied on macOS alone.

    :param grant: The standing grant, whose ``network`` and ``web`` widen the defaults.
    :param layout: The run's folders.
    :param local_binding: Let commands listen on a port and reach every port on localhost,
        which on macOS includes every other service listening there.
    :param mode: The permission mode.
    :param plugins: The plugin folders loaded, which the sandbox lets commands read.
    :param project: The project folder.
    :param reads: More folders sandboxed commands may read.
    :param system: ``sys.platform`` of the machine the run starts on.
    :returns: The settings, as ``--settings`` takes them.
    """
    web = grant.web if grant else "docs"
    fetch = {
        "docs": [f"WebFetch(domain:{domain})" for domain in _DOCS_DOMAINS],
        "open": ["WebFetch"],
        "off": [],
    }[web]
    protected = (
        project / grant_.FILE_NAME,
        project / ".mcp.json",
        layout.check,
        layout.grant,
        layout.log,
        layout.mcp,
        layout.profile,
        layout.status,
    )
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
            "allow": [
                *(tool for tool in _TOOLS if tool not in _FILE_WRITERS + ("WebFetch",)),
                f"Edit(/{project}/**)",
                f"Edit(/{layout.work}/**)",
                *fetch,
            ],
            "defaultMode": mode,
            "deny": [
                *_SECRET_READS,
                *(f"Edit(/{path})" for path in protected),
                *(f"Edit(/{plugin}/**)" for plugin in plugins),
                "Edit(~/.claude/**)",
                "Edit(~/.config/**)",
                *(["WebFetch"] if web == "off" else []),
            ],
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
                    str(layout.check),
                    str(transcripts),
                    *(str(plugin) for plugin in plugins),
                    *_TOOLCHAIN_READS,
                    *reads,
                ],
                "allowWrite": [str(layout.work)],
                "denyWrite": [
                    *(str(path) for path in protected),
                    *(str(p) for p in plugins),
                    *_session_temp_folders(system),
                ],
                "denyRead": [
                    "~/",
                    *(["/Volumes"] if system == "darwin" else []),
                    *_TOOLCHAIN_SECRETS,
                    *_session_temp_folders(system),
                ],
            },
            "network": {
                "allowLocalBinding": local_binding,
                "allowedDomains": sorted(
                    {*_PACKAGE_DOMAINS, *(grant.network if grant else ())}
                ),
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


def _text_of(content: object) -> str:
    """Return a tool result's text, whether a string or a list of text blocks.

    :param content: The result's ``content``.
    :returns: Its text.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            str(block.get("text", "")) for block in content if isinstance(block, dict)
        )
    return ""


def read_tool_calls(lines: collections.abc.Iterable[str]) -> Probed:
    """Return a session's init record, tool calls with their results, and its cost.

    :param lines: The session's stream-json output.
    :returns: What it showed; a call with no result has an empty, failed one.
    """
    init: dict[str, typing.Any] | None = None
    uses: dict[str, tuple[str, dict[str, typing.Any]]] = {}
    results: dict[str, tuple[str, bool]] = {}
    cost = decimal.Decimal(0)
    ended = False
    for line in lines:
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if not isinstance(record, dict):
            continue
        kind = record.get("type")
        if kind == "system" and record.get("subtype") == "init":
            init = record
        if kind == "result":
            cost += decimal.Decimal(str(record.get("total_cost_usd") or 0))
            ended = True
        message = record.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        for block in content if isinstance(content, list) else ():
            if not isinstance(block, dict):
                continue
            if kind == "assistant" and block.get("type") == "tool_use":
                given = block.get("input")
                uses[str(block.get("id"))] = (
                    str(block.get("name")),
                    given if isinstance(given, dict) else {},
                )
            if kind == "user" and block.get("type") == "tool_result":
                results[str(block.get("tool_use_id"))] = (
                    _text_of(block.get("content")),
                    bool(block.get("is_error")),
                )
    return Probed(
        calls=[
            ToolCall(
                failed=results.get(key, ("", True))[1],
                input=given,
                name=name,
                result=results.get(key, ("", True))[0],
            )
            for key, (name, given) in uses.items()
        ],
        cost_usd=cost,
        ended=ended,
        init=init,
    )


def _attempts(
    probe: Probe, calls: collections.abc.Sequence[ToolCall]
) -> list[ToolCall]:
    """Return the calls that made a probe exactly as given and ran it to its end.

    :param probe: The probe.
    :param calls: Every call the session made.
    :returns: Each call of the probe's tool whose input holds every field of the probe's
        with the same value and nothing else but a description, so a call sent to the
        background is not one, and whose result does not say it was moved to the
        background or timed out.
    """
    return [
        call
        for call in calls
        if call.name == probe.tool
        and all(call.input.get(key) == value for key, value in probe.input.items())
        and set(call.input) - set(probe.input) <= {"description"}
        and not _UNFINISHED.search(call.result)
    ]


def judge_preflight(
    plan: PreflightPlan,
    probed: Probed,
    *,
    servers: collections.abc.Set[str],
) -> list[str]:
    """Return what the preflight found wrong, or nothing where the profile held.

    Each check in the script counts as refused only where the script's own output for
    this exact command, run to its end, says so and nothing it should not have written
    exists; a check with no line, a script changed, a call left unmade, or any command or
    file write the launcher did not ask for fails, since the launcher cannot tell those
    from a sandbox that let it through. The script sits where nothing in the session can
    write, so its output is the sandbox's answer, not the model's.

    :param plan: The script, its checks and the tool calls the session was told to make.
    :param probed: What the session showed.
    :param servers: The MCP servers the owner's configuration names, the only ones allowed.
    :returns: One line per check or call that got through or was never finished, and per
        connector or MCP server loaded that the owner did not name.
    """
    if probed.init is None or not probed.ended:
        return [
            "the session ended without its init record or its result, so it proves nothing"
        ]
    loaded = [
        str(server.get("name"))
        for server in probed.init.get("mcp_servers") or []
        if isinstance(server, dict)
    ]
    tools = [
        str(t).split("__")[1]
        for t in probed.init.get("tools") or []
        if str(t).startswith("mcp__") and str(t).count("__") >= 2
    ]
    found = [
        f"a connector or MCP server was loaded that the configuration does not name: {name}"
        for name in dict.fromkeys(loaded + tools)
        if name not in servers
    ]
    for probe in plan.probes:
        tried = _attempts(probe, probed.calls)
        if (probe.written is not None and probe.written.exists()) or any(
            probe.through and re.search(probe.through, call.result)
            for call in probed.calls
            if call.name == probe.tool and probe.marker in json.dumps(call.input)
        ):
            found.append(f"{probe.name}: got through")
        elif not tried:
            found.append(f"{probe.name}: not tried")
    planned = (plan.run, *plan.probes)
    found += [
        f"a call the preflight did not ask for: {call.name}"
        for call in probed.calls
        if call.name in _WRITERS
        and not any(_attempts(probe, [call]) for probe in planned)
    ]
    ran = _attempts(plan.run, probed.calls)
    if not ran:
        found.append(f"{plan.run.name}: not tried")
    shown = ran[-1].result if ran else ""
    lines = set(shown.splitlines())
    if _digest(plan.script) != plan.digest:
        found.append("the preflight's script was changed before it ran")
    for check in plan.checks:
        said = {f"check {check.key} {word}" for word in ("closed", "open")} & lines
        if check.written is not None and check.written.exists():
            found.append(f"{check.name}: got through")
        elif not said:
            found.append(f"{check.name}: not finished")
        elif check.written is None and f"check {check.key} open" in said:
            found.append(f"{check.name}: got through")
    return found


def _digest(path: pathlib.Path) -> str:
    """Return a file's SHA-256, or nothing where it cannot be read.

    :param path: The file.
    :returns: The hex digest, empty for a missing or unreadable file.
    """
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def _write_script(path: pathlib.Path, checks: collections.abc.Sequence[Check]) -> str:
    """Write the preflight's script, and return its SHA-256.

    It prints one neutral line per check and the PATH, never what a check read, so the
    session that runs it handles no decoy's contents and no credential. It holds no
    apostrophe outside a quoted word, since the guard hook refuses a script it cannot
    parse, a lone quote included.

    :param path: Where to write it, a folder the sandbox lets commands read.
    :param checks: What it tries.
    :returns: The digest the launcher holds it to.
    """
    blocks = [
        f"if {{ {check.shell}; }} >/dev/null 2>&1; then echo 'check {check.key} open'; "
        f"else echo 'check {check.key} closed'; fi"
        for check in checks
    ]
    path.write_text(
        "#!/bin/sh\n"
        "# The launcher preflight: checks that the sandbox around this session refuses\n"
        "# what it must, against decoys the launcher planted a moment ago. Each check\n"
        "# prints check KEY closed or check KEY open, never what it read; no line prints\n"
        "# a credential or the contents of a file.\n"
        + "\n".join(blocks)
        + f'\necho "{_PATH_PREFIX}$PATH"\n',
        encoding="utf-8",
    )
    return _digest(path)


def _plan_preflight(
    layout: Layout,
    *,
    allowed: collections.abc.Sequence[str],
    home: pathlib.Path,
    other: pathlib.Path,
    system: str,
) -> PreflightPlan:
    """Return what the preflight tries, with its decoys and script in place.

    Every decoy is the launcher's own file holding a random token and nothing else. The
    command-side checks run inside one script the launcher writes, so the session is asked
    for one plain command and two file-tool calls, never for commands that read like
    reaching for secrets, which a model declines even against a decoy; the checks that need
    a model's own judgement to make, such as printing a ``.env`` or searching the keychain,
    are put to the guard hook by the launcher itself (``check_guard``).

    :param layout: The run's folders: the writes aim at the launcher's own folder, which
        a run must not change, and the script sits read-only in its ``check`` folder,
        which commands may read and nothing in the session may write.
    :param allowed: The hosts the profile lets commands reach.
    :param home: A new folder in the home folder for the decoys a run must not read.
    :param other: A new folder shaped like another session's temp folder.
    :param system: ``sys.platform`` of the machine the run starts on.
    :returns: The plan.
    """
    owned = layout.root / "decoy"
    for folder in (home, owned, other, layout.check):
        folder.mkdir(mode=0o700, parents=True, exist_ok=True)

    def decoy(path: pathlib.Path) -> str:
        token = secrets.token_hex(12)
        path.write_text(f"decoy {token}\n", encoding="utf-8")
        return token

    host = next(
        h for h in ("example.com", "example.net", "example.org") if h not in allowed
    )
    quote = shlex.quote
    checks = [
        Check(
            key="home-read",
            name="reading a decoy in the home folder with a command",
            shell=f"grep -q {decoy(home / 'home.txt')} {quote(str(home / 'home.txt'))}",
        ),
        Check(
            key="network",
            name=f"reaching {host}, a host the profile does not list",
            shell=f"curl -sS -m 20 -o /dev/null -w '%{{http_code}}' https://{host}/ | grep -q '^[23]'",
        ),
        Check(
            key="launcher-write",
            name="writing to the launcher's own folder with a command",
            shell=f"touch {quote(str(owned / 'written-by-command'))}",
            written=owned / "written-by-command",
        ),
        Check(
            key="temp-read",
            name="reading a decoy in another session's temp folder",
            shell=f"grep -q {decoy(other / 'session.txt')} {quote(str(other / 'session.txt'))}",
        ),
        Check(
            key="temp-append",
            name="appending to a file in another session's temp folder",
            shell=f"echo x >> {quote(str(other / 'append.txt'))}",
            written=other / "append.txt",
        ),
        Check(
            key="temp-create",
            name="creating a file in another session's temp folder",
            shell=f"touch {quote(str(other / 'created'))}",
            written=other / "created",
        ),
        *(
            [
                Check(
                    key="keychain",
                    name="reaching the login keychain with a command",
                    shell="security show-keychain-info",
                )
            ]
            if system == "darwin"
            else []
        ),
        Check(
            key="credential",
            name="showing a command the Claude credential, in its environment or a process's",
            shell=(
                'test -n "${CLAUDE_CODE_OAUTH_TOKEN:-}${ANTHROPIC_API_KEY:-}" || grep -qas '
                "-e CLAUDE_CODE_OAUTH_TOKEN= -e ANTHROPIC_API_KEY= /proc/[0-9]*/environ"
            ),
        ),
        Check(key="sudo", name="gaining root with sudo", shell="sudo -n true"),
    ]
    script = layout.check / "preflight.sh"
    digest = _write_script(script, checks)
    script.chmod(0o400)
    command = f"sh {quote(str(script))}"
    run = Probe(
        input={"command": command},
        marker=command,
        name="running the launcher's preflight script",
        through="",
        tool="Bash",
    )
    probes = [
        Probe(
            input={"file_path": str(home / "home-tool.txt")},
            marker=str(home / "home-tool.txt"),
            name="reading a decoy in the home folder with the Read tool",
            through=decoy(home / "home-tool.txt"),
            tool="Read",
        ),
        Probe(
            input={"file_path": str(owned / "written-by-tool"), "content": "x"},
            marker=str(owned / "written-by-tool"),
            name="writing to the launcher's own folder with the Write tool",
            through="",
            tool="Write",
            written=owned / "written-by-tool",
        ),
    ]
    return PreflightPlan(
        checks=checks, digest=digest, probes=probes, run=run, script=script
    )


def check_seen_path(
    plan: PreflightPlan,
    probed: Probed,
    *,
    forbidden: collections.abc.Sequence[pathlib.Path],
) -> list[str]:
    """Return what is unsafe on the PATH a command inside the run actually sees.

    Claude Code adds folders of its own, such as each plugin's ``bin/``, so the PATH the
    launcher passes is checked again as the preflight's script printed it.

    :param plan: The preflight's plan, whose script prints the PATH last.
    :param probed: What the session showed.
    :param forbidden: The folders the run can write or the launcher must keep clean.
    :returns: Each unsafe entry; nothing where the script did not run, which the
        preflight's judgement already reports.
    """
    ran = _attempts(plan.run, probed.calls)
    if not ran:
        return []
    seen = [
        line.strip()
        for line in ran[-1].result.splitlines()
        if line.strip().startswith(_PATH_PREFIX)
    ]
    if not seen:
        return ["the preflight's script printed no PATH"]
    return check_path(seen[-1].removeprefix(_PATH_PREFIX), forbidden=forbidden)


def check_path(
    path: str, *, forbidden: collections.abc.Sequence[pathlib.Path]
) -> list[str]:
    """Return each PATH entry a run could plant a program in, or nothing where none is.

    Hooks and the launcher's own calls find their programs through the run's PATH outside
    the sandbox, so an entry the run can write would let it run a program as the owner.

    :param path: The PATH the run would get.
    :param forbidden: The folders the run can write or the launcher must keep clean: the
        project, the run's folder and its scratch folder.
    :returns: One line per entry that is empty, relative, or inside one of those folders
        or a temp folder.
    """
    roots = [
        pathlib.Path(os.path.realpath(root))
        for root in (*forbidden, tempfile.gettempdir(), *_TEMP_FOLDERS)
    ]
    found = []
    for entry in path.split(os.pathsep):
        if not entry or not os.path.isabs(entry):
            found.append(f"PATH entry {entry or '(empty)'} is not an absolute folder")
            continue
        real = pathlib.Path(os.path.realpath(entry))
        if any(real == root or real.is_relative_to(root) for root in roots):
            found.append(
                f"PATH entry {entry} is a folder the run can write or a temp folder"
            )
    return found


def _probe_prompt(
    kind: str, intro: str, probes: collections.abc.Sequence[Probe]
) -> str:
    """Return the prompt that tells a probe session which calls to make.

    :param kind: ``PREFLIGHT`` or ``GATE``, which also names the session in its prompt.
    :param intro: What the calls are for.
    :param probes: The calls.
    :returns: The prompt.
    """
    calls = [{"tool": probe.tool, "input": probe.input} for probe in probes]
    return (
        f"LAUNCHER-{kind}\n\n{intro} Make each call below exactly as given, once, in "
        "order, with the tool named; do not retry a call that fails or is refused, do "
        "not change or combine calls, and do not explain. When every call is made, "
        "reply `done`.\n\n```json\n" + json.dumps(calls, indent=1) + "\n```\n"
    )


def _run_probe_session(prompt: str, *, kind: str, session: Session) -> Probed:
    """Run a short session on the probe model under the run profile, and read it back.

    Each session writes a log of its own, opened fresh, so nothing an earlier session
    showed can satisfy a later check.

    :param prompt: What it must do.
    :param kind: ``preflight`` or ``gate``, which names its log in the run's folder.
    :param session: How to start ``claude``.
    :returns: What it showed; a session past its time shows only what it printed, and
        counts as not ended.
    """
    identity = str(uuid.uuid4())
    log = session.layout.root / f"{kind}-{identity}.jsonl"
    command = build_command(
        claude=session.claude,
        layout=session.layout,
        limits_left=Limits(budget_usd=decimal.Decimal("0.50"), max_turns=40),
        model=_PROBE_MODEL,
        plugins=session.plugins,
        prompt=prompt,
        resume=False,
        session=identity,
    )
    timed_out = False
    with log.open("x", encoding="utf-8") as out:
        try:
            subprocess.run(
                command,
                check=False,
                cwd=session.project,
                env=session.environment | _PROBE_ENVIRONMENT,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                stdout=out,
                timeout=_PROBE_SECONDS,
            )
        except subprocess.TimeoutExpired:
            timed_out = True
    with log.open(encoding="utf-8") as lines:
        probed = read_tool_calls(lines)
    return dataclasses.replace(probed, ended=probed.ended and not timed_out)


def check_guard(session: Session, *, init: dict[str, typing.Any] | None) -> list[str]:
    """Return what the loaded guard hook let through of the calls a model will not make.

    Each call is put to the guard exactly as Claude Code puts it, as a ``PreToolUse``
    input on standard input under the run's environment, so a guard missing, broken or
    asking where it must refuse shows here.

    :param session: The run's plugins, environment and project.
    :param init: The preflight session's init record, which lists the plugins it loaded.
    :returns: One line per call it did not refuse; one line if no guard is loaded.
    """
    guarded = [
        plugin
        for plugin in session.plugins
        if (plugin / "skills" / "secure-project" / "scripts" / "guard.sh").is_file()
    ]
    loaded = {
        str(entry.get("path"))
        for entry in (init or {}).get("plugins") or []
        if isinstance(entry, dict)
    }
    if not guarded or str(guarded[0]) not in loaded:
        return ["no guard hook is loaded: the session did not load manage-project"]
    scripts = [guarded[0] / "skills" / "secure-project" / "scripts" / "guard.sh"]
    missing = f"claude-preflight-{secrets.token_hex(6)}"
    calls = (
        ("printing a .env file", "Bash", {"command": "cat .env"}),
        ("reading a key file", "Read", {"file_path": "deploy/server.pem"}),
        (
            "searching the keychain",
            "Bash",
            {"command": f"security find-generic-password -s {missing} -w"},
        ),
        (
            "sending mail through a connector",
            "mcp__mail__send_message",
            {"to": "someone@example.com", "body": "decoy"},
        ),
        ("a force-push", "Bash", {"command": "git push --force origin main"}),
    )
    found = []
    for name, tool, given in calls:
        payload = {
            "cwd": str(session.project),
            "hook_event_name": "PreToolUse",
            "permission_mode": "dontAsk",
            "session_id": "launcher-preflight",
            "tool_input": given,
            "tool_name": tool,
        }
        try:
            done = subprocess.run(
                ["/bin/sh", str(scripts[0])],
                capture_output=True,
                check=False,
                cwd=session.project,
                env=session.environment | {"CLAUDE_PROJECT_DIR": str(session.project)},
                input=json.dumps(payload),
                text=True,
                timeout=60,
            )
            decision = json.loads(done.stdout or "{}").get("hookSpecificOutput", {})
        except (OSError, ValueError, subprocess.TimeoutExpired):
            decision = {}
        if decision.get("permissionDecision") != "deny":
            found.append(f"{name}: the guard hook did not refuse it")
    return found


def preflight(
    session: Session,
    *,
    allowed: collections.abc.Sequence[str],
    servers: collections.abc.Set[str],
    system: str,
) -> tuple[list[str], decimal.Decimal]:
    """Try the forbidden things under the run profile, then remove the decoys and script.

    :param session: How to start ``claude``, with the run's profile and environment.
    :param allowed: The hosts the profile lets commands reach.
    :param servers: The MCP servers the owner's configuration names.
    :param system: ``sys.platform`` of the machine the run starts on.
    :returns: What got through or went untried, empty where the profile held, and what
        the session cost.
    """
    home = (
        pathlib.Path.home() / ".cache" / "claude-preflight" / session.layout.root.name
    )
    forbidden = (session.project, session.layout.root, session.layout.work)
    other = (
        pathlib.Path("/tmp")
        / f"claude-{os.getuid()}"
        / f"-launcher-decoy-{secrets.token_hex(6)}"
    )
    plan: PreflightPlan | None = None
    try:
        plan = _plan_preflight(
            session.layout, allowed=allowed, home=home, other=other, system=system
        )
        probed = _run_probe_session(
            _probe_prompt("PREFLIGHT", _PREFLIGHT_INTRO, [plan.run, *plan.probes]),
            kind="preflight",
            session=session,
        )
        return [
            *judge_preflight(plan, probed, servers=servers),
            *check_seen_path(plan, probed, forbidden=forbidden),
            *check_guard(session, init=probed.init),
        ], probed.cost_usd
    finally:
        for folder in (
            home,
            session.layout.root / "decoy",
            other,
            session.layout.check,
        ):
            shutil.rmtree(folder, ignore_errors=True)
        if plan is not None:
            for written in (*plan.checks, *plan.probes):
                if written.written is not None and written.written.is_file():
                    written.written.unlink()


def _verification_ids(plan: str) -> list[str]:
    """Return the IDs of the plan's Verification lines.

    :param plan: The text of ``PLAN.md``.
    :returns: Each bold label opening a bullet under ``### Verification``.
    """
    section = re.search(
        r"^### Verification\s*$(.*?)(?=^#{1,3} )", plan + "\n# ", re.M | re.S
    )
    if not section:
        return []
    return [
        match.group(1).strip()
        for line in section.group(1).splitlines()
        if (match := _VERIFICATION_LINE.match(line))
    ]


def _check_records(
    project: pathlib.Path, *, commits: collections.abc.Set[str], today: datetime.date
) -> list[str]:
    """Return what the project's records lack for the build to count as finished.

    Every acceptance row for a Verification line must carry an ISO date no later than
    today, in order, so a pass cannot follow a later fail; the last must be a pass, run on
    a commit the build now stands on.

    :param project: The project folder.
    :param commits: The commits an acceptance row may name: the current one, and its
        parent where the current commit changed only the records.
    :param today: Today's date, in UTC.
    :returns: One line per record missing and per Verification line whose rows do not
        hold.
    """
    found = [
        f"{name} is missing"
        for name in _RECORDS
        if (project / name).is_symlink() or not (project / name).is_file()
    ]
    if "PLAN.md is missing" in found:
        return found
    ids = _verification_ids((project / "PLAN.md").read_text(encoding="utf-8"))
    if not ids:
        return [*found, "PLAN.md has no Verification lines"]
    rows: dict[str, list[dict[str, str]]] = {line: [] for line in ids}
    table = project / "verification.csv"
    if table.is_file() and not table.is_symlink():
        with table.open(encoding="utf-8", newline="") as lines:
            for row in csv.DictReader(lines):
                line = (row.get("line") or "").strip()
                if (row.get("stage") or "").strip() == "acceptance" and line in rows:
                    rows[line].append(row)
    for line, held in rows.items():
        found += _check_rows(line, held, commits=commits, today=today)
    return found


def _check_rows(
    line: str,
    rows: collections.abc.Sequence[dict[str, str]],
    *,
    commits: collections.abc.Set[str],
    today: datetime.date,
) -> list[str]:
    """Return why one Verification line's acceptance rows do not show it passing.

    :param line: The line's ID.
    :param rows: Its acceptance rows, in the file's order.
    :param commits: The commits a row may name.
    :param today: Today's date, in UTC.
    :returns: The findings, empty where the line passes.
    """
    if not rows:
        return [f"verification.csv has no acceptance row for {line}"]
    dates = []
    for row in rows:
        try:
            dates.append(datetime.date.fromisoformat((row.get("date") or "").strip()))
        except ValueError:
            return [
                f"verification.csv has an acceptance row for {line} with no ISO date"
            ]
    if any(date > today for date in dates):
        return [
            f"verification.csv has an acceptance row for {line} with a date after today"
        ]
    if dates != sorted(dates):
        return [f"verification.csv's acceptance rows for {line} are out of date order"]
    last = rows[-1]
    commit = (last.get("commit") or "").strip().lower()
    if (last.get("result") or "").strip() != "pass":
        return [f"verification.csv's last acceptance row for {line} is not a pass"]
    if len(commit) < 7 or not any(full.startswith(commit) for full in commits):
        return [
            f"verification.csv's last acceptance row for {line} names a commit the build is not on"
        ]
    return []


def _read_commits(result: str) -> set[str]:
    """Return the commits an acceptance row may name, from the gate's HEAD probe.

    :param result: What ``_HEAD_COMMAND`` printed: the current commit and its parent,
        then the files the current commit changed, then the end marker.
    :returns: The current commit, with its parent where the current commit changed only
        the records; empty where the output is not that shape.
    """
    lines = [line.strip() for line in result.splitlines() if line.strip()]
    if _HEAD_END not in lines:
        return set()
    lines = lines[: lines.index(_HEAD_END)]
    hashes = [line.lower() for line in lines if re.fullmatch(r"[0-9a-fA-F]{40}", line)]
    changed = set(lines[len(hashes) :])
    if not hashes:
        return set()
    if len(hashes) > 1 and changed and changed <= _RECORD_FILES:
        return set(hashes[:2])
    return {hashes[0]}


def _uncommitted(result: str) -> list[str]:
    """Return what ``git status --porcelain`` shows as uncommitted, less the placeholders.

    On Linux the sandbox holds a write denial on a file that does not exist with an empty
    placeholder while each command runs, so the gate's own ``git status`` lists Claude
    Code's protected names and the grant as untracked (Claude Code 2.1.330,
    ubuntu-24.04); none of them is a file the run can write, so an untracked entry by
    one of those names is not the run's work. A status without its end marker shows
    itself, so it fails.

    :param result: What the status command printed.
    :returns: Each line that is uncommitted work, or the output where the marker is missing.
    """
    lines = [line.rstrip() for line in result.splitlines() if line.strip()]
    if _STATUS_END not in lines:
        return lines or ["git status printed nothing"]
    return [
        line
        for line in lines[: lines.index(_STATUS_END)]
        if not (line.startswith("?? ") and line[3:].rstrip("/") in _PLACEHOLDERS)
    ]


def gate(
    session: Session, *, commands: collections.abc.Sequence[str]
) -> tuple[list[str], decimal.Decimal]:
    """Return why the build is not finished, or nothing where the launcher's gate passes.

    The launcher executes nothing from the project after a run: it reads the records as
    data, and everything that runs in the project's tree — ``git status`` for uncommitted
    work, ``git log`` for the commit the records must name, and each gate command such
    as the suite — runs in a probe session under the run profile, so a hostile ``.git``,
    filter or test runs only inside the sandbox. A command passes only where the stream
    shows it run exactly as given, to its end, with no error, and the whole gate fails
    closed when the session ends without its result or a record cannot be read.

    :param session: How to start ``claude``.
    :param commands: The commands that must pass, such as the suite.
    :returns: The findings, and what the gate's session cost.
    """
    status = Probe(
        input={"command": _STATUS_COMMAND},
        marker=_STATUS_COMMAND,
        name="uncommitted work",
        through="",
        tool="Bash",
    )
    head = Probe(
        input={"command": _HEAD_COMMAND},
        marker=_HEAD_COMMAND,
        name="the current commit",
        through="",
        tool="Bash",
    )
    probes = [
        status,
        head,
        *(
            Probe(input={"command": c}, marker=c, name=c, through="", tool="Bash")
            for c in commands
        ),
    ]
    probed = _run_probe_session(
        _probe_prompt("GATE", "This session runs the launcher's gate.", probes),
        kind="gate",
        session=session,
    )
    found = [] if probed.ended else ["the gate's session ended without its result"]
    commits: set[str] = set()
    for probe in probes:
        tried = _attempts(probe, probed.calls)
        if not tried:
            found.append(f"`{probe.name}` was not run")
        elif probe is status and (tried[-1].failed or _uncommitted(tried[-1].result)):
            shown = _uncommitted(tried[-1].result)
            found.append(
                f"uncommitted work: {' '.join(shown)[:200] or 'git status failed'}"
            )
        elif probe is head:
            commits = set() if tried[-1].failed else _read_commits(tried[-1].result)
        elif tried[-1].failed:
            found.append(f"`{probe.name}` failed: {tried[-1].result.strip()[-200:]}")
    try:
        found += _check_records(
            session.project,
            commits=commits,
            today=datetime.datetime.now(datetime.UTC).date(),
        )
    except (OSError, UnicodeError, ValueError, csv.Error) as failure:
        found.append(
            f"the records could not be read: {type(failure).__name__}: {failure}"[:300]
        )
    return found, probed.cost_usd


def _count_responses(
    path: pathlib.Path,
) -> tuple[decimal.Decimal, set[str], decimal.Decimal]:
    """Return the priced responses, their ids and the results' total in a stream or transcript.

    :param path: A transcript, or the launcher's log of every invocation's stream.
    :returns: The list-price dollars of the distinct responses, their ids, and the sum of
        ``total_cost_usd`` over the result records.
    """
    prices = costs._prices()
    priced: dict[str, decimal.Decimal] = {}
    results = decimal.Decimal(0)
    if not path.exists():
        return decimal.Decimal(0), set(), results
    with path.open(encoding="utf-8") as lines:
        for line in lines:
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if not isinstance(record, dict):
                continue
            message = record.get("message")
            if record.get("type") == "assistant" and isinstance(message, dict):
                parsed = costs._parse_message(message, agent="", effort="")
                dollars = costs._price_message(parsed, prices=prices)
                identity = str(message.get("id") or record.get("uuid"))
                priced[identity] = dollars or decimal.Decimal(0)
            if record.get("type") == "result":
                results += decimal.Decimal(str(record.get("total_cost_usd") or 0))
    return sum(priced.values(), decimal.Decimal(0)), set(priced), results


def measure(session: str, log: pathlib.Path) -> tuple[decimal.Decimal, int]:
    """Return a run's list-price spend and turns so far, the larger of two records.

    Both live where the run cannot write: the session's transcripts under
    ``~/.claude/projects``, outside every folder the run's file tools and sandbox reach,
    and the launcher's own log of the stream it captured, in the run folder beside them;
    so a run that hid its spend from one still meets the limit through the other.
    A turn is one response of the session's own model loop, as ``--max-turns`` counts
    them, subagents' responses not counted; the result's ``num_turns`` counts tool calls
    instead, so forty calls made in parallel in one response read as 41 there and 1 here.
    The launcher passes ``--max-turns`` too, but it resets on each resume.

    :param session: The session's id.
    :param log: The launcher's log of every invocation's stream.
    :returns: The dollars, subagents included, and the turns.
    """
    found = sorted(
        (pathlib.Path.home() / ".claude" / "projects").glob(f"*/{session}.jsonl")
    )
    transcript_spent = decimal.Decimal(0)
    transcript_ids: set[str] = set()
    if found:
        rows = costs.total_session(found[0])
        transcript_spent = sum(
            (decimal.Decimal(row["dollars"]) for row in rows if row["dollars"]),
            decimal.Decimal(0),
        )
        transcript_ids = _count_responses(found[0])[1]
    stream_spent, stream_ids, results = _count_responses(log)
    spent = max(transcript_spent, stream_spent, results)
    return spent, max(len(transcript_ids), len(stream_ids))


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
        is_error=result.get("is_error") is True,
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
                spent, turns = measure(session, layout.log)
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
    if outcome.is_error and _USAGE_LIMIT.search(outcome.text):
        return "limit", (
            "the plan's usage limit was reached and resets later than "
            "--usage-wait-hours allows"
        )
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
    accept: collections.abc.Callable[[], list[str]],
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

    :param accept: The launcher's gate, run when the session says it finished: what it
        returns is why the finish is not accepted, and the session is resumed to fix it.
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
        spent, measured = measure(session, layout.log)
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
        if state == "finished":
            findings = accept()
            if findings:
                state = "resume"
                detail = "the launcher's gate did not pass: " + "; ".join(findings)
            else:
                detail = "the run ended with its marker and the launcher's gate passed"
        if state != "resume":
            final_spent, measured = measure(session, layout.log)
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


def _read_grant_bytes(path: pathlib.Path) -> bytes:
    """Return a grant file's bytes, refusing a symlink.

    A symlink is refused wherever it points, since what counts is where the grant was
    found, and a link in the project can point anywhere the run chooses.

    :param path: The grant file.
    :returns: Its content.
    :raises LaunchError: If it is a symlink or not a regular file.
    """
    if path.is_symlink():
        raise LaunchError(f"{path} is a symlink; a grant must be a regular file")
    if not path.is_file():
        raise LaunchError(f"{path} is not a regular file")
    return path.read_bytes()


def _read_approvals(approvals: pathlib.Path) -> list[tuple[str, str, str]]:
    """Return the owner's approvals: each grant's hash, its project and when.

    :param approvals: The file of approvals, outside anything a run can write.
    :returns: One entry per line; none where the file is absent.
    """
    if not approvals.exists():
        return []
    entries = (
        line.split("\t") for line in approvals.read_text(encoding="utf-8").splitlines()
    )
    return [(fields[0], fields[1], fields[2]) for fields in entries if len(fields) == 3]


def _is_approved(
    content: bytes, *, approvals: pathlib.Path, project: pathlib.Path
) -> bool:
    """Return whether the owner approved exactly this grant for exactly this project.

    :param content: The grant's bytes.
    :param approvals: The file of approvals.
    :param project: The project folder, resolved.
    :returns: True where the hash is the one recorded for this project.
    """
    digest = hashlib.sha256(content).hexdigest()
    return any(
        entry[0] == digest and entry[1] == str(project)
        for entry in _read_approvals(approvals)
    )


def describe_grant(grant: grant_.Grant, *, project: pathlib.Path) -> str:
    """Return what a grant lets an unattended run do, in plain words.

    :param grant: The grant.
    :param project: The project it is for.
    :returns: A few lines the owner reads before approving it.
    """

    def listed(items: collections.abc.Sequence[str], none: str) -> str:
        return ", ".join(items) if items else none

    budget = (
        f"up to ${grant.budget_usd:.2f}"
        if grant.budget_usd is not None
        else "no more than the command line's --budget-usd"
    )
    turns = f" and {grant.max_turns} turns" if grant.max_turns is not None else ""
    web = {
        "docs": "documentation sites only",
        "off": "no site",
        "open": "any site",
    }[grant.web]
    accounts = [f"{a.provider} {a.account} ({a.tier})" for a in grant.accounts]
    return "\n".join(
        (
            f"Grant for {project}, given by {grant.given_by} on {grant.given_on}, "
            f"valid until {grant.expires_on}.",
            f"- A run may spend {budget}{turns}.",
            f"- It may push to: {listed(grant.remotes, 'no remote')}.",
            f"- Its environment holds these secrets: {listed(grant.secrets, 'none')}.",
            "- Its commands may reach, besides PyPI and npm: "
            f"{listed(grant.network, 'no other host')}.",
            f"- It may fetch web pages from {web}.",
            f"- Accounts it reaches through those secrets: {listed(accounts, 'none listed')}.",
            "- What a secret lets the run do is set by that secret's scope at its issuer, "
            "not by this file; no grant covers moving money, deleting anything or "
            "loosening a data class.",
        )
    )


def approve_grant(
    path: pathlib.Path,
    *,
    approvals: pathlib.Path,
    confirm: collections.abc.Callable[[str], bool],
    project: pathlib.Path,
) -> str:
    """Record the owner's approval of a grant for a project, replacing that project's last.

    :param path: The grant file the owner has read.
    :param approvals: The file of approvals.
    :param confirm: Shown the grant's summary, says whether the owner approves it.
    :param project: The project folder, resolved.
    :returns: The hash recorded.
    :raises LaunchError: If the grant is a symlink, malformed, expired, changed while it
        was read, or not confirmed.
    """
    content = _read_grant_bytes(path)
    try:
        grant = grant_.read_grant(path)
    except grant_.GrantError as failure:
        raise LaunchError(str(failure)) from failure
    if _read_grant_bytes(path) != content:
        raise LaunchError(f"{path} changed while it was read; approve it again")
    if not confirm(describe_grant(grant, project=project)):
        raise LaunchError(
            "not approved: confirm with y, or pass --yes after reading it"
        )
    digest = hashlib.sha256(content).hexdigest()
    kept = [entry for entry in _read_approvals(approvals) if entry[1] != str(project)]
    lines = [
        *("\t".join(entry) for entry in kept),
        "\t".join((digest, str(project), _now())),
    ]
    approvals.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    staged = approvals.with_suffix(".tmp")
    staged.write_text("\n".join(lines) + "\n", encoding="utf-8")
    staged.chmod(0o600)
    staged.replace(approvals)
    return digest


def _prepare(
    *,
    approvals: pathlib.Path,
    grant_path: pathlib.Path | None,
    mcp_config: pathlib.Path | None,
    project: pathlib.Path,
    runs: pathlib.Path,
) -> tuple[Layout, grant_.Grant | None]:
    """Return the run's folders, made, with the grant snapshot and MCP configuration in place.

    :param approvals: The file of grant hashes the owner approved.
    :param grant_path: The grant to snapshot, if any.
    :param mcp_config: The MCP servers the project needs, if any.
    :param project: The project folder.
    :param runs: The folder that holds every run's own folder, outside any temp folder.
    :returns: The layout and the grant read from the snapshot.
    :raises LaunchError: If the grant is a symlink, malformed, expired, or not approved
        for this project, wherever it was found.
    """
    home = pathlib.Path.home().resolve()
    if not runs.resolve().is_relative_to(home):
        raise LaunchError(
            f"{runs} is outside the home folder; the run folder holds the launcher's own "
            "files and must sit where the profile denies a run access, such as the "
            "default ~/.cache/claude-runs, not a temp folder the sandbox lets it write"
        )
    stamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
    root = runs / f"{project.name}-{stamp}-{uuid.uuid4().hex[:6]}"
    layout = Layout(root=root, work=root / "work")
    layout.work.mkdir(parents=True, mode=0o700)
    root.chmod(0o700)
    grant = None
    if grant_path is not None:
        content = _read_grant_bytes(grant_path)
        if not _is_approved(content, approvals=approvals, project=project):
            raise LaunchError(
                f"{grant_path} is not approved for {project}: read it, then run "
                "launch.py --approve-grant"
            )
        layout.grant.write_bytes(content)
        layout.grant.chmod(0o400)
        try:
            grant = grant_.read_grant(layout.grant)
        except grant_.GrantError as failure:
            raise LaunchError(str(failure)) from failure
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
    dot_git = project / ".git"
    if os.path.lexists(dot_git) and (dot_git.is_symlink() or not dot_git.is_dir()):
        raise LaunchError(
            f"{dot_git} is not a folder; a symlink or gitfile there could point git at "
            "configuration that runs code, so the launcher will not touch it"
        )
    commands: list[list[str]] = []
    if not dot_git.exists():
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
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("prompt", nargs="?", type=pathlib.Path, help="the prompt file")
    parser.add_argument(
        "--approvals",
        type=pathlib.Path,
        default=pathlib.Path.home() / ".config" / "claude-grants" / "approved",
        help="the file of grant hashes the owner approved, outside anything a run writes",
    )
    parser.add_argument(
        "--approve-grant",
        action="store_true",
        help="record the project's grant as read and approved, then exit",
    )
    parser.add_argument(
        "--allow-local-binding",
        action="store_true",
        help="let commands listen on ports and reach every port on localhost, other "
        "services included (macOS; Linux needs no flag for a server the run starts)",
    )
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
        "--gate-command",
        action="append",
        default=[],
        help="a command, such as the suite, that must pass in the sandbox before a "
        "finish is accepted",
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
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="prove the profile with the preflight, report, and start no run",
    )
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
    parser.add_argument(
        "--usage-wait-hours",
        type=float,
        default=5.0,
        help="the longest a request waits for the plan's usage window to reset",
    )
    arguments = parser.parse_args()
    project = arguments.project.resolve()
    if arguments.approve_grant:
        grant_path = arguments.grant or project / grant_.FILE_NAME
        try:
            digest = approve_grant(
                grant_path,
                approvals=arguments.approvals,
                confirm=_confirm,
                project=project,
            )
        except (LaunchError, OSError) as failure:
            raise SystemExit(f"launch: {failure}") from failure
        print(f"approved {grant_path} (sha256 {digest})")
        return
    if arguments.prompt is None:
        parser.error("the prompt file is required")
    try:
        prompt = arguments.prompt.read_text(encoding="utf-8")
        found = project / grant_.FILE_NAME
        grant_path = arguments.grant or (found if os.path.lexists(found) else None)
        layout, grant = _prepare(
            approvals=arguments.approvals,
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
        local_binding=arguments.allow_local_binding,
        mode=arguments.permission_mode,
        plugins=plugins,
        project=project,
        reads=arguments.allow_read,
        system=sys.platform,
    )
    layout.profile.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    layout.profile.chmod(0o400)
    environment = build_environment(
        grant=grant,
        layout=layout,
        source=os.environ,
        usage_wait_hours=arguments.usage_wait_hours,
    )
    unsafe = check_path(
        environment.get("PATH", ""), forbidden=(project, layout.root, layout.work)
    )
    if unsafe:
        raise SystemExit(
            "launch: " + "; ".join(unsafe) + "; hooks outside the sandbox find their "
            "programs on it, so remove the entry (deactivate a virtual environment) first"
        )
    print(f"launch: run folder {layout.root}", file=sys.stderr)
    if arguments.dry_run:
        command = build_command(
            claude=arguments.claude, layout=layout, limits_left=limits, model=arguments.model,
            plugins=plugins, prompt="<prompt>", resume=False, session="<session>",
        )  # fmt: skip
        print(shlex.join(command))
        print("environment:", " ".join(sorted(environment)))
        return
    session = Session(
        claude=arguments.claude,
        environment=environment,
        layout=layout,
        plugins=plugins,
        project=project,
    )
    versions = {
        "cli_version": _read_cli_version(arguments.claude),
        "release": _read_release(),
    }
    probe_spend = [decimal.Decimal(0)]
    found: list[str] = []

    def accept() -> list[str]:
        findings, spent = gate(session, commands=arguments.gate_command)
        probe_spend[0] += spent
        return findings

    try:
        servers = set(
            json.loads(layout.mcp.read_text(encoding="utf-8")).get("mcpServers") or {}
        )
        found, cost = preflight(
            session,
            allowed=profile["sandbox"]["network"]["allowedDomains"],
            servers=servers,
            system=sys.platform,
        )
        probe_spend[0] += cost
        if found or arguments.preflight_only:
            report = Report(
                detail=(
                    "the preflight found the profile open: " + "; ".join(found)
                    if found
                    else "the preflight passed; no run started (--preflight-only)"
                ),
                invocations=0,
                session="none",
                spent_usd=decimal.Decimal(0),
                state="failed" if found else "finished",
                turns=0,
            )
        else:
            report = run(
                accept=accept,
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
    except Exception as failure:  # noqa: BLE001 - the owner must hear of any failure
        report = Report(
            detail=f"the launcher failed: {type(failure).__name__}: {failure}"[:300],
            invocations=0,
            session="unknown",
            spent_usd=decimal.Decimal(0),
            state="failed",
            turns=0,
        )

    record = (
        dataclasses.asdict(report)
        | versions
        | {
            "ended": _now(),
            "preflight": "passed" if not found else found,
            "probe_spent_usd": f"{probe_spend[0]:.2f}",
            "spent_usd": f"{report.spent_usd:.2f}",
        }
    )
    layout.status.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(report.line())
    _notify(arguments.notify, report.line())
    raise SystemExit(_EXIT[report.state])


def _confirm(summary: str) -> bool:
    """Show a grant's summary and return whether the owner approves it at a terminal.

    Approval needs a person typing at a terminal, so no script or session piping in an
    answer can approve a grant.

    :param summary: What the grant allows.
    :returns: True only for a ``y`` typed at a terminal.
    """
    print(summary)
    if not sys.stdin.isatty():
        print("approving a grant needs a terminal: run it yourself, not from a script")
        return False
    return input("Approve this grant? [y/N] ").strip().lower() in ("y", "yes")


def _read_cli_version(claude: str) -> str:
    """Return the version of the ``claude`` the run starts, or ``unknown``.

    :param claude: The executable.
    :returns: Its version number.
    """
    try:
        done = subprocess.run(
            [claude, "--version"],
            capture_output=True,
            check=False,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    words = done.stdout.split()
    return words[0] if done.returncode == 0 and words else "unknown"


def _read_release() -> str:
    """Return the house plugins' release: the checkout's tag description, or the version.

    :returns: ``git describe`` of the marketplace checkout this script runs from, such
        as ``v0.6`` or ``v0.6-3-gabc1234-dirty``; else the plugin manifest's version.
    """
    root = _SKILLS.parent.parent.parent
    if (root / ".git").exists():
        done = subprocess.run(
            [
                "git", "-c", "core.fsmonitor=false", "-C", str(root),
                "describe", "--tags", "--always", "--dirty",
            ],
            capture_output=True, check=False, text=True, timeout=60,
        )  # fmt: skip
        if done.returncode == 0 and done.stdout.strip():
            return done.stdout.strip()
    manifest = _SKILLS.parent / ".claude-plugin" / "plugin.json"
    try:
        return "plugin " + str(
            json.loads(manifest.read_text(encoding="utf-8"))["version"]
        )
    except (OSError, KeyError, ValueError):
        return "unknown"


if __name__ == "__main__":
    main()
