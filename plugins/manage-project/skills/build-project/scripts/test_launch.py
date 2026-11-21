# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest"]
# ///
"""Tests for launch.py, run with ``uv run --script test_launch.py``.

A fake ``claude`` stands in for the real one. A run's invocation takes the next outcome
from a scenario file, appends a priced response to the session's transcript under a
throwaway home, and prints the stream-json result Claude Code 2.1.330 prints, or nothing
for a drop. A preflight or gate session prints the init record and a tool call and result
for each probe it was asked to make, refused, passed or leaked as the test sets.
"""

import json
import os
import pathlib
import subprocess
import sys
import textwrap

import pytest

_HERE = pathlib.Path(__file__).resolve().parent
_PLUGIN = _HERE.parents[2]

_FAKE = textwrap.dedent(
    """\
    import json, os, pathlib, shlex, sys, time
    home = pathlib.Path(os.environ["HOME"])
    argv = sys.argv[1:]

    def log(kind):
        with (home / "calls.jsonl").open("a") as out:
            out.write(json.dumps({"argv": argv, "env": sorted(os.environ), "kind": kind}) + "\\n")

    def mode(name, default):
        path = home / name
        return path.read_text().strip() if path.exists() else default

    def emit(record):
        print(json.dumps(record), flush=True)

    if argv == ["--version"]:
        log("version")
        print("9.9.9 (Claude Code)")
        sys.exit(0)
    prompt = argv[-1]
    if "LAUNCHER-PREFLIGHT" in prompt or "LAUNCHER-GATE" in prompt:
        kind = "preflight" if "LAUNCHER-PREFLIGHT" in prompt else "gate"
        log(kind)
        behaviour = mode(f"{kind}.txt", "refuse" if kind == "preflight" else "pass")
        servers = [{"name": "mail", "status": "connected"}] if behaviour == "connector" else []
        plugins = [{"name": "p", "path": argv[n + 1]} for n, a in enumerate(argv) if a == "--plugin-dir"]
        emit({"type": "system", "subtype": "init", "tools": ["Bash", "Read"], "mcp_servers": servers,
              "plugins": plugins})
        for n, probe in enumerate(json.loads(prompt.split("```json")[1].split("```")[0])):
            if behaviour == "skip":
                continue
            emit({"type": "assistant", "message": {"id": f"m{n}", "content": [
                {"type": "tool_use", "id": f"t{n}", "name": probe["tool"], "input": probe["input"]}]}})
            text, failed = "Permission denied by the sandbox", True
            if kind == "gate":
                text, failed = ("1 failed", True) if behaviour == "fail" else ("3 passed", False)
            elif behaviour == "leak" and probe["tool"] in ("Read", "Bash"):
                path = probe["input"].get("file_path") or shlex.split(probe["input"]["command"])[-1]
                if pathlib.Path(path).exists():
                    text, failed = pathlib.Path(path).read_text(), False
            emit({"type": "user", "message": {"content": [
                {"type": "tool_result", "tool_use_id": f"t{n}", "content": text, "is_error": failed}]}})
        emit({"type": "result", "subtype": "success", "result": "done", "num_turns": 2,
              "total_cost_usd": 0.01, "session_id": "probe"})
        sys.exit(0)
    log("run")
    scenario = home / "scenario.txt"
    outcomes = scenario.read_text().split()
    outcome, rest = outcomes[0], outcomes[1:]
    scenario.write_text(" ".join(rest))
    session = argv[argv.index("--session-id" if "--session-id" in argv else "--resume") + 1]
    transcript = home / ".claude" / "projects" / "-fake" / f"{session}.jsonl"
    transcript.parent.mkdir(parents=True, exist_ok=True)

    def spend(dollars, n):
        record = {"type": "assistant", "timestamp": "2026-11-21T10:00:00Z",
                  "message": {"id": f"{session}-{n}-{time.time_ns()}", "model": "claude-opus-5-5",
                              "usage": {"input_tokens": int(dollars * 250_000)}}}
        with transcript.open("a") as out:
            out.write(json.dumps(record) + "\\n")

    def result(subtype, text="", turns=3):
        emit({"type": "result", "subtype": subtype, "result": text,
              "num_turns": turns, "total_cost_usd": 0.10, "session_id": session})

    if outcome == "spin_stream":
        for n in range(200):
            emit({"type": "assistant", "message": {"id": f"s-{n}", "model": "claude-opus-5-5",
                  "usage": {"input_tokens": 25_000}}})
            time.sleep(0.1)
        sys.exit(0)
    if outcome == "spin":
        for n in range(200):
            spend(0.10, n)
            time.sleep(0.1)
        sys.exit(0)
    spend(0.10, 0)
    if outcome == "drop":
        sys.exit(1)
    if outcome == "finished":
        result("success", "All done.\\nLAUNCHER: finished")
    elif outcome == "blocked":
        result("success", "Stopped.\\nLAUNCHER: blocked: the owner must create the repository")
    elif outcome == "nomarker":
        result("success", "I will carry on later.", turns=5)
    elif outcome == "usage":
        result("success", "You've hit your session limit · resets 3pm")
    else:
        result(outcome)
    """
)

_PLAN = """# Thing

## Delivery

### Verification

- **R1** — the suite passes.
- **Acceptance** — the thing runs from a fresh clone.

### Milestones

- [x] **M1 Thing** — R1; done when it runs.
"""

_RECORDS = {
    "DEPENDENCIES.md": "# Dependencies\n\nThe plan is PLAN.md.\n",
    "costs.csv": "stage,model,dollars\nM1,sonnet,1.00\n",
    "verification.csv": (
        "command,commit,date,line,printed,result,stage\n"
        "uv run pytest,abc1234,2026-11-21,R1,3 passed,pass,acceptance\n"
        "uv run thing,abc1234,2026-11-21,Acceptance,ok,pass,acceptance\n"
    ),
}


def _commit_all(folder: pathlib.Path) -> None:
    for command in (
        ["git", "init", "-q", "-b", "main"],
        ["git", "add", "-A"],
        [
            "git",
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@example.com",
            "commit",
            "-q",
            "-m",
            "x",
        ],
    ):
        subprocess.run(command, cwd=folder, check=True, capture_output=True)


def _make_project(folder: pathlib.Path, records: dict[str, str]) -> pathlib.Path:
    folder.mkdir()
    (folder / "prompt.md").write_text("Build the thing.\n")
    (folder / "PLAN.md").write_text(_PLAN)
    for name, text in records.items():
        (folder / name).write_text(text)
    _commit_all(folder)
    return folder


@pytest.fixture
def home(tmp_path: pathlib.Path) -> pathlib.Path:
    folder = tmp_path / "home"
    folder.mkdir()
    return folder


@pytest.fixture
def fake_claude(tmp_path: pathlib.Path) -> pathlib.Path:
    script = tmp_path / "fake_claude.py"
    script.write_text(_FAKE)
    wrapper = tmp_path / "claude"
    wrapper.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n')
    wrapper.chmod(0o755)
    return wrapper


@pytest.fixture
def project(tmp_path: pathlib.Path) -> pathlib.Path:
    return _make_project(tmp_path / "project", _RECORDS)


@pytest.fixture
def unrecorded(tmp_path: pathlib.Path) -> pathlib.Path:
    return _make_project(tmp_path / "unrecorded", {})


def _launch(
    home: pathlib.Path,
    fake_claude: pathlib.Path,
    project: pathlib.Path,
    scenario: str,
    *extra: str,
    environment: dict[str, str] | None = None,
    plugin: pathlib.Path = _PLUGIN,
) -> subprocess.CompletedProcess[str]:
    (home / "scenario.txt").write_text(scenario)
    return subprocess.run(
        [
            sys.executable,
            str(_HERE / "launch.py"),
            str(project / "prompt.md"),
            "--project",
            str(project),
            "--claude",
            str(fake_claude),
            "--runs-dir",
            str(home / "runs"),
            "--plugin-dir",
            str(plugin),
            "--poll-seconds",
            "0.2",
            "--retry-wait",
            "0.01",
            *extra,
        ],
        capture_output=True,
        check=False,
        env={"HOME": str(home), "PATH": os.environ["PATH"]} | (environment or {}),
        text=True,
        timeout=120,
    )


def _calls(home: pathlib.Path, kind: str = "run") -> list[dict[str, list[str]]]:
    lines = (home / "calls.jsonl").read_text().splitlines()
    return [call for call in map(json.loads, lines) if call["kind"] == kind]


def _status(home: pathlib.Path) -> dict[str, object]:
    return json.loads(next((home / "runs").glob("*/status.json")).read_text())


def _argument(argv: list[str], flag: str) -> str:
    return argv[argv.index(flag) + 1]


def _profile(home: pathlib.Path) -> dict[str, dict[str, object]]:
    return json.loads(
        pathlib.Path(_argument(_calls(home)[0]["argv"], "--settings")).read_text()
    )


def test_when_run_finishes_and_gate_passes_then_exit_zero(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    done = _launch(home, fake_claude, project, "finished", "--budget-usd", "5")
    assert (done.returncode, done.stdout.split(":")[0]) == (0, "finished")


def test_when_run_starts_then_isolated_flags_passed(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    _launch(home, fake_claude, project, "finished", "--budget-usd", "5")
    argv = _calls(home)[0]["argv"]
    assert {"--restricted", "--strict-mcp-config", "--session-id"} <= set(argv) and (
        _argument(argv, "--permission-prompts") == "none"
    )


def test_when_run_starts_then_profile_sandboxes_and_drops_connectors(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    _launch(home, fake_claude, project, "finished", "--budget-usd", "5")
    profile = _profile(home)
    assert (
        profile["sandbox"]["enabled"],
        profile["sandbox"]["allowUnsandboxedCommands"],
        profile["disableClaudeAiConnectors"],
        profile["sandbox"]["filesystem"]["denyRead"][0],
    ) == (True, False, True, "~/")


def test_when_no_local_binding_flag_then_profile_leaves_it_off(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    _launch(home, fake_claude, project, "finished", "--budget-usd", "5")
    assert _profile(home)["sandbox"]["network"].get("allowLocalBinding", False) is False


def test_when_local_binding_flag_then_profile_allows_it(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    _launch(
        home,
        fake_claude,
        project,
        "finished",
        "--budget-usd",
        "5",
        "--allow-local-binding",
    )
    assert _profile(home)["sandbox"]["network"]["allowLocalBinding"] is True


def test_when_run_drops_then_same_session_resumed(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    done = _launch(home, fake_claude, project, "drop finished", "--budget-usd", "5")
    first, second = (call["argv"] for call in _calls(home))
    assert (done.returncode, _argument(second, "--resume")) == (
        0,
        _argument(first, "--session-id"),
    )


def test_when_run_resumed_then_budget_passed_is_what_is_left(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    _launch(home, fake_claude, project, "drop finished", "--budget-usd", "5")
    budgets = [_argument(call["argv"], "--max-budget-usd") for call in _calls(home)]
    assert budgets == ["5.00", "4.90"]


def test_when_final_message_lacks_marker_then_resumed(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    done = _launch(home, fake_claude, project, "nomarker finished", "--budget-usd", "5")
    assert (done.returncode, len(_calls(home))) == (0, 2)


def test_when_run_blocked_then_exit_three_with_reason(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    done = _launch(home, fake_claude, project, "blocked", "--budget-usd", "5")
    assert (done.returncode, "create the repository" in done.stdout) == (3, True)


def test_when_claude_reports_budget_reached_then_limit(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    done = _launch(
        home, fake_claude, project, "error_max_budget_usd", "--budget-usd", "5"
    )
    assert (done.returncode, done.stdout.split(":")[0]) == (4, "limit")


def test_when_plan_usage_limit_hit_then_limit_without_resuming(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    done = _launch(home, fake_claude, project, "usage finished", "--budget-usd", "5")
    assert (done.returncode, len(_calls(home)), "usage limit" in done.stdout) == (
        4,
        1,
        True,
    )


def test_when_run_starts_then_usage_window_waited_out_by_claude(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    _launch(home, fake_claude, project, "finished", "--budget-usd", "5")
    names = set(_calls(home)[0]["env"])
    assert {
        "CLAUDE_CODE_RETRY_WATCHDOG",
        "CLAUDE_CODE_RETRY_WATCHDOG_MAX_USAGE_LIMIT_WAIT_MS",
        "CLAUDE_CODE_RETRY_WATCHDOG_USAGE_LIMIT_RECHECK_MS",
    } <= names


def test_when_transcript_passes_budget_then_run_stopped(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    done = _launch(home, fake_claude, project, "spin", "--budget-usd", "1")
    assert (done.returncode, _status(home)["detail"]) == (
        4,
        "the spend limit was reached",
    )


def test_when_transcript_passes_turns_then_run_stopped(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    done = _launch(
        home, fake_claude, project, "spin", "--budget-usd", "100", "--max-turns", "10"
    )
    assert (done.returncode, _status(home)["detail"]) == (
        4,
        "the turn limit was reached",
    )


def test_when_turns_used_up_then_limit_before_next_invocation(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    done = _launch(
        home,
        fake_claude,
        project,
        "nomarker finished",
        "--budget-usd",
        "5",
        "--max-turns",
        "1",
    )
    assert (done.returncode, len(_calls(home))) == (4, 1)


def test_when_drops_exceed_resumes_then_failed(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    done = _launch(
        home,
        fake_claude,
        project,
        "drop drop drop finished",
        "--budget-usd",
        "5",
        "--max-resumes",
        "2",
    )
    assert (done.returncode, len(_calls(home))) == (5, 3)


def test_when_no_spend_limit_then_refused(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    done = _launch(home, fake_claude, project, "finished")
    assert (done.returncode, "no spend limit" in done.stderr) == (1, True)


def test_when_run_ends_then_status_names_cli_version_and_release(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    _launch(home, fake_claude, project, "finished", "--budget-usd", "5")
    status = _status(home)
    assert (status["cli_version"], bool(status["release"])) == ("9.9.9", True)


def test_when_records_missing_then_finish_not_accepted(
    home: pathlib.Path, fake_claude: pathlib.Path, unrecorded: pathlib.Path
) -> None:
    done = _launch(
        home,
        fake_claude,
        unrecorded,
        "finished",
        "--budget-usd",
        "5",
        "--max-resumes",
        "0",
    )
    assert (done.returncode, "DEPENDENCIES.md" in done.stdout) == (5, True)


def test_when_gate_fails_then_run_resumed_with_reason(
    home: pathlib.Path, fake_claude: pathlib.Path, unrecorded: pathlib.Path
) -> None:
    _launch(home, fake_claude, unrecorded, "finished finished", "--budget-usd", "5")
    resumed = _calls(home)[1]["argv"][-1]
    assert "gate" in resumed and "verification.csv" in resumed


def test_when_acceptance_row_failed_then_finish_not_accepted(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    rows = project / "verification.csv"
    rows.write_text(
        rows.read_text()
        + "uv run thing,def5678,2026-11-22,Acceptance,boom,fail,acceptance\n"
    )
    _commit_all(project)
    done = _launch(
        home,
        fake_claude,
        project,
        "finished",
        "--budget-usd",
        "5",
        "--max-resumes",
        "0",
    )
    assert (done.returncode, "Acceptance" in done.stdout) == (5, True)


def test_when_work_left_uncommitted_then_finish_not_accepted(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    (project / "loose.py").write_text("x = 1\n")
    done = _launch(
        home,
        fake_claude,
        project,
        "finished",
        "--budget-usd",
        "5",
        "--max-resumes",
        "0",
    )
    assert (done.returncode, "uncommitted" in done.stdout) == (5, True)


def test_when_gate_command_fails_then_finish_not_accepted(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    (home / "gate.txt").write_text("fail")
    done = _launch(
        home, fake_claude, project, "finished", "--budget-usd", "5",
        "--max-resumes", "0", "--gate-command", "uv run pytest -q",
    )  # fmt: skip
    assert (done.returncode, "uv run pytest -q" in done.stdout) == (5, True)


def test_when_gate_command_passes_then_finished(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    done = _launch(
        home, fake_claude, project, "finished", "--budget-usd", "5",
        "--gate-command", "uv run pytest -q",
    )  # fmt: skip
    assert (done.returncode, len(_calls(home, "gate"))) == (0, 1)


def test_when_preflight_refuses_every_probe_then_run_starts(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    _launch(home, fake_claude, project, "finished", "--budget-usd", "5")
    preflight = _calls(home, "preflight")
    assert (len(preflight), _argument(preflight[0]["argv"], "--model")) == (1, "haiku")


@pytest.mark.parametrize(
    ("behaviour", "said"),
    [("leak", "got through"), ("connector", "connector"), ("skip", "not tried")],
)
def test_when_preflight_not_clean_then_run_refused(
    home: pathlib.Path,
    fake_claude: pathlib.Path,
    project: pathlib.Path,
    behaviour: str,
    said: str,
) -> None:
    (home / "preflight.txt").write_text(behaviour)
    done = _launch(home, fake_claude, project, "finished", "--budget-usd", "5")
    assert (done.returncode, said in done.stdout, len(_calls(home))) == (5, True, 0)


def test_when_guard_not_loaded_then_run_refused(
    home: pathlib.Path,
    fake_claude: pathlib.Path,
    project: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    done = _launch(
        home, fake_claude, project, "finished", "--budget-usd", "5", plugin=tmp_path
    )
    assert (done.returncode, "no guard hook" in done.stdout) == (5, True)


def test_when_runs_folder_outside_home_then_refused(
    home: pathlib.Path,
    fake_claude: pathlib.Path,
    project: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    done = _launch(
        home, fake_claude, project, "finished", "--budget-usd", "5",
        "--runs-dir", str(tmp_path / "runs"),
    )  # fmt: skip
    assert (done.returncode, "home folder" in done.stderr) == (1, True)


def test_when_preflight_ends_then_decoys_removed(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    _launch(home, fake_claude, project, "finished", "--budget-usd", "5")
    run = next((home / "runs").iterdir())
    left = [
        *run.rglob("decoy*"),
        *run.rglob("*.pem"),
        *home.glob(".cache/claude-preflight/*"),
    ]
    assert left == []


def _approve(
    home: pathlib.Path, project: pathlib.Path, *extra: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(_HERE / "launch.py"),
            "--approve-grant",
            "--project",
            str(project),
            *extra,
        ],
        capture_output=True,
        check=False,
        env={"HOME": str(home), "PATH": os.environ["PATH"]},
        stdin=subprocess.DEVNULL,
        text=True,
        timeout=60,
    )


def _write_grant(project: pathlib.Path, **extra: object) -> pathlib.Path:
    path = project / "grant.json"
    path.write_text(
        json.dumps(
            {
                "expires_on": "2999-01-01",
                "given_by": "owner",
                "given_on": "2026-11-21",
                "remotes": ["github.com/owner/thing"],
                "run": {"budget_usd": 1.5, "max_turns": 40},
                "secrets": ["PROJECT_TOKEN"],
            }
            | extra
        )
    )
    return path


@pytest.fixture
def unapproved(project: pathlib.Path) -> pathlib.Path:
    return _write_grant(project)


@pytest.fixture
def grant(home: pathlib.Path, project: pathlib.Path) -> pathlib.Path:
    path = _write_grant(project)
    _approve(home, project, "--yes")
    return path


def test_when_grant_approved_then_summary_says_what_it_allows(
    home: pathlib.Path, project: pathlib.Path, unapproved: pathlib.Path
) -> None:
    done = _approve(home, project, "--yes")
    assert all(
        phrase in done.stdout
        for phrase in ("github.com/owner/thing", "PROJECT_TOKEN", "$1.50", "2999-01-01")
    )


def test_when_approval_not_confirmed_then_grant_not_approved(
    home: pathlib.Path,
    fake_claude: pathlib.Path,
    project: pathlib.Path,
    unapproved: pathlib.Path,
) -> None:
    _approve(home, project)
    done = _launch(home, fake_claude, project, "finished", "--budget-usd", "5")
    assert (done.returncode, "not approved" in done.stderr) == (1, True)


def test_when_grant_lists_account_actions_then_refused(
    home: pathlib.Path, project: pathlib.Path
) -> None:
    _write_grant(
        project,
        accounts=[
            {
                "provider": "GitHub",
                "account": "o",
                "tier": "free",
                "actions": ["deploy"],
            }
        ],
    )
    done = _approve(home, project, "--yes")
    assert (done.returncode != 0, "actions" in done.stderr) == (True, True)


def test_when_project_grant_not_approved_then_refused(
    home: pathlib.Path,
    fake_claude: pathlib.Path,
    project: pathlib.Path,
    unapproved: pathlib.Path,
) -> None:
    done = _launch(home, fake_claude, project, "finished", "--budget-usd", "5")
    assert (done.returncode, "not approved" in done.stderr) == (1, True)


def test_when_project_grant_changed_after_approval_then_refused(
    home: pathlib.Path,
    fake_claude: pathlib.Path,
    project: pathlib.Path,
    grant: pathlib.Path,
) -> None:
    grant.write_text(
        grant.read_text().replace('"secrets"', '"network": ["evil.example"], "secrets"')
    )
    done = _launch(home, fake_claude, project, "finished", "--budget-usd", "5")
    assert (done.returncode, "not approved" in done.stderr) == (1, True)


def test_when_project_grant_is_symlink_to_outside_then_refused(
    home: pathlib.Path,
    fake_claude: pathlib.Path,
    project: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    real = _write_grant(outside)
    (project / "grant.json").symlink_to(real)
    _approve(home, outside, "--yes")
    done = _launch(home, fake_claude, project, "finished", "--budget-usd", "5")
    assert done.returncode == 1


def test_when_same_grant_approved_for_other_project_then_refused(
    home: pathlib.Path,
    fake_claude: pathlib.Path,
    project: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    other = tmp_path / "other"
    other.mkdir()
    _write_grant(other)
    _approve(home, other, "--yes")
    _write_grant(project)
    done = _launch(home, fake_claude, project, "finished", "--budget-usd", "5")
    assert (done.returncode, "not approved" in done.stderr) == (1, True)


def test_when_grant_reapproved_then_earlier_version_no_longer_approved(
    home: pathlib.Path,
    fake_claude: pathlib.Path,
    project: pathlib.Path,
    grant: pathlib.Path,
) -> None:
    first = grant.read_text()
    grant.write_text(first.replace('"secrets"', '"network": ["pypi.org"], "secrets"'))
    _approve(home, project, "--yes")
    grant.write_text(first)
    done = _launch(home, fake_claude, project, "finished", "--budget-usd", "5")
    assert (done.returncode, "not approved" in done.stderr) == (1, True)


def test_when_run_starts_then_file_tools_scoped_and_grant_and_plugins_denied(
    home: pathlib.Path,
    fake_claude: pathlib.Path,
    project: pathlib.Path,
    grant: pathlib.Path,
) -> None:
    _launch(home, fake_claude, project, "finished", "--budget-usd", "5")
    profile = _profile(home)
    allow, deny = profile["permissions"]["allow"], profile["permissions"]["deny"]
    deny_write = profile["sandbox"]["filesystem"]["denyWrite"]
    assert (
        {"Edit", "Write", "NotebookEdit"} & set(allow),
        f"Edit(/{project}/**)" in allow,
        "Edit(~/.claude/**)" in deny,
        f"Edit(/{project}/grant.json)" in deny,
        f"Edit(/{_PLUGIN}/**)" in deny,
        str(project / "grant.json") in deny_write,
        str(_PLUGIN) in deny_write,
    ) == (set(), True, True, True, True, True, True)


def test_when_stream_shows_budget_spent_though_transcript_does_not_then_stopped(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    done = _launch(home, fake_claude, project, "spin_stream", "--budget-usd", "1")
    assert (done.returncode, done.stdout.split(":")[0]) == (4, "limit")


def test_when_grant_lower_than_command_line_then_grant_caps_budget(
    home: pathlib.Path,
    fake_claude: pathlib.Path,
    project: pathlib.Path,
    grant: pathlib.Path,
) -> None:
    _launch(home, fake_claude, project, "finished", "--budget-usd", "5")
    argv = _calls(home)[0]["argv"]
    assert (_argument(argv, "--max-budget-usd"), _argument(argv, "--max-turns")) == (
        "1.50",
        "40",
    )


def test_when_grant_names_secret_then_only_it_passed(
    home: pathlib.Path,
    fake_claude: pathlib.Path,
    project: pathlib.Path,
    grant: pathlib.Path,
) -> None:
    _launch(
        home,
        fake_claude,
        project,
        "finished",
        environment={"OTHER_TOKEN": "x", "PROJECT_TOKEN": "y", "MAIL_PASSWORD": "z"},
    )
    names = set(_calls(home)[0]["env"])
    assert (
        "PROJECT_TOKEN" in names,
        "OTHER_TOKEN" in names,
        "MAIL_PASSWORD" in names,
    ) == (
        True,
        False,
        False,
    )


def test_when_run_starts_then_background_wait_unbounded_and_guard_denies(
    home: pathlib.Path,
    fake_claude: pathlib.Path,
    project: pathlib.Path,
    grant: pathlib.Path,
) -> None:
    _launch(home, fake_claude, project, "finished")
    names = set(_calls(home)[0]["env"])
    assert {
        "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS",
        "CLAUDE_GUARD",
        "CLAUDE_GRANT_FILE",
    } <= names


def test_when_grant_expired_then_refused(
    home: pathlib.Path,
    fake_claude: pathlib.Path,
    project: pathlib.Path,
    grant: pathlib.Path,
) -> None:
    grant.write_text(grant.read_text().replace("2999-01-01", "2000-01-01"))
    done = _launch(home, fake_claude, project, "finished", "--budget-usd", "5")
    assert (done.returncode, "expired" in done.stderr) == (1, True)


def test_when_notify_given_then_report_line_handed_to_it(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    sink = home / "notified.txt"
    notifier = home / "notify.sh"
    notifier.write_text(f'#!/bin/sh\nprintf "%s" "$1" > "{sink}"\n')
    notifier.chmod(0o755)
    _launch(
        home,
        fake_claude,
        project,
        "finished",
        "--budget-usd",
        "5",
        "--notify",
        str(notifier),
    )
    assert sink.read_text().startswith("finished:")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q", *sys.argv[1:]]))
