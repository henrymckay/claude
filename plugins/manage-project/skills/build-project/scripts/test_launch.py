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
    import json, os, pathlib, shlex, subprocess, sys, time
    home = pathlib.Path(os.environ["HOME"])
    argv = sys.argv[1:]

    def log(kind):
        with (home / "calls.jsonl").open("a") as out:
            out.write(json.dumps({"argv": argv, "env": sorted(os.environ), "kind": kind}) + "\\n")

    def mode(name, default):
        path = home / name
        tokens = path.read_text().split() if path.exists() else []
        if not tokens:
            return default
        if len(tokens) > 1:
            path.write_text(" ".join(tokens[1:]))
        return tokens[0]

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
        servers = {"connector": [{"name": "mail", "status": "connected"}],
                   "docsserver": [{"name": "docs", "status": "connected"}]}.get(behaviour, [])
        plugins = [{"name": "p", "path": argv[n + 1]} for n, a in enumerate(argv) if a == "--plugin-dir"]
        emit({"type": "system", "subtype": "init", "tools": ["Bash", "Read"], "mcp_servers": servers,
              "plugins": plugins})
        status = mode("status.txt", "clean") if kind == "gate" else ""
        for n, probe in enumerate(json.loads(prompt.split("```json")[1].split("```")[0])):
            if behaviour == "skip":
                continue
            given = dict(probe["input"])
            if behaviour == "near":
                given = {k: v + " " for k, v in given.items()}
            if behaviour == "background":
                given["run_in_background"] = True
            emit({"type": "assistant", "message": {"id": f"m{n}", "content": [
                {"type": "tool_use", "id": f"t{n}", "name": probe["tool"], "input": given}]}})
            text, failed = "Permission denied by the sandbox", True
            command = probe["input"].get("command", "")
            if kind == "gate" and command.startswith("git status") and status == "dirty":
                text, failed = "?? loose.py\\nporcelain-end", False
            elif kind == "gate" and command.startswith("git ") and pathlib.Path(".git").is_file():
                text, failed = "fatal: the stand-in sandbox runs no planted git", True
            elif kind == "gate" and command.startswith("git "):
                done = subprocess.run(command, shell=True, capture_output=True, text=True)
                text, failed = done.stdout + done.stderr, done.returncode != 0
            elif command.startswith('echo "path-probe='):
                seen = f"{os.getcwd()}/.venv/bin:/usr/bin" if behaviour == "badpath" else "/usr/bin:/bin"
                text, failed = f"path-probe={seen}", False
            elif kind == "gate" and behaviour == "moved":
                text, failed = "Command was moved to the background with ID: b1. Output is being written to: x", False
            elif kind == "gate":
                text, failed = ("1 failed", True) if behaviour == "fail" else ("3 passed", False)
            elif behaviour.startswith("echo:") and command.endswith(f"echo {behaviour[5:]}"):
                text, failed = behaviour[5:], False
            elif (behaviour == "leak" or (behaviour == "leaktemp" and "-launcher-decoy" in command)) and probe["tool"] in ("Read", "Bash"):
                path = probe["input"].get("file_path") or shlex.split(probe["input"]["command"])[-1]
                if pathlib.Path(path).exists():
                    text, failed = pathlib.Path(path).read_text(), False
            emit({"type": "user", "message": {"content": [
                {"type": "tool_result", "tool_use_id": f"t{n}", "content": text, "is_error": failed}]}})
        if behaviour != "noresult":
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
        emit({"type": "result", "subtype": "success", "is_error": True,
              "result": "You've hit your session limit · resets 3pm", "num_turns": 1,
              "total_cost_usd": 0.10, "session_id": session})
    elif outcome == "usagetext":
        result("success", "Noted: You've hit your session limit is a message I handle.\\nLAUNCHER: finished")
    elif outcome == "finishedrec":
        pathlib.Path("DEPENDENCIES.md").write_text("# Dependencies\\n")
        pathlib.Path("costs.csv").write_text("stage,model,dollars\\n")
        pathlib.Path("verification.csv").write_text(
            "command,commit,date,line,printed,result,stage\\n"
            "t,abc,2026-11-21,R1,ok,pass,acceptance\\n"
            "t,abc,2026-11-21,Acceptance,ok,pass,acceptance\\n"
        )
        result("success", "All done.\\nLAUNCHER: finished")
    elif outcome == "hostile":
        evil = pathlib.Path.cwd().parent / "evil.git"
        os.rename(".git", evil)
        pathlib.Path(".git").write_text(f"gitdir: {evil}\\n")
        with (evil / "config").open("a") as config:
            config.write(f'[filter "evil"]\\n\\tclean = touch {home / "marker"}\\n')
            config.write(f"[core]\\n\\tfsmonitor = touch {home / 'marker'}\\n")
        pathlib.Path(".gitattributes").write_text("* filter=evil\\n")
        time.sleep(1.1)
        pathlib.Path("prompt.md").write_text("changed\\n")
        result("success", "All done.\\nLAUNCHER: finished")
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
        "uv run pytest,{commit},2026-11-21,R1,3 passed,pass,acceptance\n"
        "uv run thing,{commit},2026-11-21,Acceptance,ok,pass,acceptance\n"
    ),
}


def _head(folder: pathlib.Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=folder,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


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
        if name != "verification.csv":
            (folder / name).write_text(text)
    _commit_all(folder)
    if "verification.csv" in records:
        rows = records["verification.csv"].replace("{commit}", _head(folder))
        (folder / "verification.csv").write_text(rows)
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


def _calls_or_none(home: pathlib.Path) -> list[dict[str, list[str]]]:
    return _calls(home) if (home / "calls.jsonl").exists() else []


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
    (home / "status.txt").write_text("dirty")
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


def test_when_run_plants_hostile_git_then_launcher_runs_none_of_it(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    _launch(
        home, fake_claude, project, "hostile", "--budget-usd", "5", "--max-resumes", "0"
    )
    assert not (home / "marker").exists()


def test_when_project_git_is_not_a_folder_then_refused(
    home: pathlib.Path,
    fake_claude: pathlib.Path,
    project: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    (project / ".git").rename(tmp_path / "moved.git")
    (project / ".git").write_text(f"gitdir: {tmp_path / 'moved.git'}\n")
    done = _launch(home, fake_claude, project, "finished", "--budget-usd", "5")
    assert (done.returncode, ".git" in done.stderr, _calls_or_none(home)) == (
        1,
        True,
        [],
    )


def test_when_gate_session_ends_without_result_then_finish_not_accepted(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    (home / "gate.txt").write_text("noresult")
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
    assert (done.returncode, "gate" in done.stdout) == (5, True)


def test_when_later_gate_session_tries_nothing_then_earlier_one_does_not_count(
    home: pathlib.Path, fake_claude: pathlib.Path, unrecorded: pathlib.Path
) -> None:
    (home / "gate.txt").write_text("pass skip")
    done = _launch(
        home, fake_claude, unrecorded, "finished finishedrec", "--budget-usd", "5",
        "--max-resumes", "1", "--gate-command", "uv run pytest -q",
    )  # fmt: skip
    assert (done.returncode, "was not run" in done.stdout) == (5, True)


def test_when_preflight_call_differs_from_probe_then_not_tried(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    (home / "preflight.txt").write_text("near")
    done = _launch(home, fake_claude, project, "finished", "--budget-usd", "5")
    assert (done.returncode, "not tried" in done.stdout) == (5, True)


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
    [
        ("leak", "got through"),
        ("leaktemp", "another session's temp folder: got through"),
        (
            "echo:credential-visible",
            "the Claude credential, in its environment or a process's: got through",
        ),
        ("echo:root-reached", "gaining root with sudo: got through"),
        ("connector", "connector"),
        ("skip", "not tried"),
    ],
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
    home: pathlib.Path,
    project: pathlib.Path,
    *extra: str,
    answer: str | None = "y",
) -> subprocess.CompletedProcess[str]:
    """Approve at a terminal answering ``answer``, or with no terminal where it is None."""
    controller, terminal = os.openpty() if answer is not None else (-1, -1)
    if answer is not None:
        os.write(controller, f"{answer}\n".encode())
    try:
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
            stdin=terminal if answer is not None else subprocess.DEVNULL,
            text=True,
            timeout=60,
        )
    finally:
        if answer is not None:
            os.close(controller)
            os.close(terminal)


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
    _approve(home, project)
    return path


def test_when_grant_approved_then_summary_says_what_it_allows(
    home: pathlib.Path, project: pathlib.Path, unapproved: pathlib.Path
) -> None:
    done = _approve(home, project)
    assert all(
        phrase in done.stdout
        for phrase in ("github.com/owner/thing", "PROJECT_TOKEN", "$1.50", "2999-01-01")
    )


@pytest.mark.parametrize(
    ("extra", "answer"), [((), "n"), ((), None), (("--yes",), None)]
)
def test_when_approval_not_confirmed_at_a_terminal_then_grant_not_approved(
    home: pathlib.Path,
    fake_claude: pathlib.Path,
    project: pathlib.Path,
    unapproved: pathlib.Path,
    extra: tuple[str, ...],
    answer: str | None,
) -> None:
    _approve(home, project, *extra, answer=answer)
    done = _launch(home, fake_claude, project, "finished", "--budget-usd", "5")
    assert (done.returncode, "not approved" in done.stderr) == (1, True)


@pytest.mark.parametrize("option", ["--approve-g", "--appro"])
def test_when_approval_option_abbreviated_then_grant_not_approved(
    home: pathlib.Path,
    fake_claude: pathlib.Path,
    project: pathlib.Path,
    unapproved: pathlib.Path,
    option: str,
) -> None:
    controller, terminal = os.openpty()
    os.write(controller, b"y\n")
    try:
        subprocess.run(
            [
                sys.executable,
                str(_HERE / "launch.py"),
                option,
                "--project",
                str(project),
            ],
            capture_output=True,
            check=False,
            env={"HOME": str(home), "PATH": os.environ["PATH"]},
            stdin=terminal,
            text=True,
            timeout=60,
        )
    finally:
        os.close(controller)
        os.close(terminal)
    done = _launch(home, fake_claude, project, "finished", "--budget-usd", "5")
    assert (done.returncode, "not approved" in done.stderr) == (1, True)


def test_when_profile_built_then_approvals_folder_unwritable_by_tools_and_commands(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    _launch(home, fake_claude, project, "finished", "--budget-usd", "5")
    profile = _profile(home)
    approvals = home / ".config" / "claude-grants" / "approved"
    writable = [
        pathlib.Path(os.path.expanduser(p))
        for p in profile["sandbox"]["filesystem"]["allowWrite"]
    ]
    edits = [
        rule[len("Edit(/") : -len("/**)")]
        for rule in profile["permissions"]["allow"]
        if rule.startswith("Edit(/")
    ]
    assert (
        "Edit(~/.config/**)" in profile["permissions"]["deny"],
        any(approvals.is_relative_to(p) for p in writable),
        any(approvals.is_relative_to(p) for p in map(pathlib.Path, edits)),
    ) == (True, False, False)


def test_when_path_starts_inside_project_then_refused(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    planted = f"{project}/.venv/bin"
    done = _launch(
        home, fake_claude, project, "finished", "--budget-usd", "5",
        environment={"PATH": f"{planted}:{os.environ['PATH']}"},
    )  # fmt: skip
    assert (done.returncode, planted in done.stderr, _calls_or_none(home)) == (
        1,
        True,
        [],
    )


def test_when_path_holds_relative_entry_then_refused(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    done = _launch(
        home, fake_claude, project, "finished", "--budget-usd", "5",
        environment={"PATH": f"node_modules/.bin:{os.environ['PATH']}"},
    )  # fmt: skip
    assert (done.returncode, "node_modules/.bin" in done.stderr) == (1, True)


def test_when_session_sees_a_writable_path_entry_then_run_refused(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    (home / "preflight.txt").write_text("badpath")
    done = _launch(home, fake_claude, project, "finished", "--budget-usd", "5")
    assert (
        done.returncode,
        f"{project}/.venv/bin" in done.stdout,
        len(_calls(home)),
    ) == (
        5,
        True,
        0,
    )


@pytest.mark.parametrize("behaviour", ["background", "moved"])
def test_when_gate_command_not_finished_in_the_foreground_then_refused(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path, behaviour: str
) -> None:
    (home / "gate.txt").write_text(behaviour)
    done = _launch(
        home, fake_claude, project, "finished", "--budget-usd", "5",
        "--max-resumes", "0", "--gate-command", "uv run pytest -q",
    )  # fmt: skip
    assert (done.returncode, "uv run pytest -q" in done.stdout) == (5, True)


def test_when_gate_runs_then_background_off_and_bash_timeout_set(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    _launch(home, fake_claude, project, "finished", "--budget-usd", "5")
    names = set(_calls(home, "gate")[0]["env"])
    assert {
        "BASH_DEFAULT_TIMEOUT_MS",
        "BASH_MAX_TIMEOUT_MS",
        "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS",
    } <= names


@pytest.mark.parametrize(
    ("rows", "said"),
    [
        (
            "t,{commit},2026-11-21,R1,ok,pass,acceptance\nt,0000000,2026-11-21,Acceptance,ok,pass,acceptance\n",
            "commit",
        ),
        (
            "t,{commit},2026-11-20,R1,x,fail,acceptance\nt,{commit},2026-11-19,R1,ok,pass,acceptance\nt,{commit},2026-11-20,Acceptance,ok,pass,acceptance\n",
            "order",
        ),
        (
            "t,{commit},2999-01-01,R1,ok,pass,acceptance\nt,{commit},2026-11-21,Acceptance,ok,pass,acceptance\n",
            "date",
        ),
        (
            "t,{commit},someday,R1,ok,pass,acceptance\nt,{commit},2026-11-21,Acceptance,ok,pass,acceptance\n",
            "date",
        ),
    ],
)
def test_when_acceptance_rows_do_not_hold_then_finish_not_accepted(
    home: pathlib.Path,
    fake_claude: pathlib.Path,
    tmp_path: pathlib.Path,
    rows: str,
    said: str,
) -> None:
    header = "command,commit,date,line,printed,result,stage\n"
    project = _make_project(
        tmp_path / "rows", _RECORDS | {"verification.csv": header + rows}
    )
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
    assert (done.returncode, said in done.stdout) == (5, True)


def test_when_mcp_config_names_a_server_then_only_it_may_load(
    home: pathlib.Path,
    fake_claude: pathlib.Path,
    project: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    config = tmp_path / "mcp.json"
    config.write_text(json.dumps({"mcpServers": {"docs": {"command": "true"}}}))
    (home / "preflight.txt").write_text("docsserver")
    allowed = _launch(
        home,
        fake_claude,
        project,
        "finished",
        "--budget-usd",
        "5",
        "--mcp-config",
        str(config),
    )
    (home / "preflight.txt").write_text("connector")
    other = _launch(
        home,
        fake_claude,
        project,
        "finished",
        "--budget-usd",
        "5",
        "--mcp-config",
        str(config),
    )
    assert (allowed.returncode, other.returncode) == (0, 5)


def test_when_final_message_only_mentions_usage_limit_then_finished(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    done = _launch(home, fake_claude, project, "usagetext", "--budget-usd", "5")
    assert (done.returncode, done.stdout.split(":")[0]) == (0, "finished")


@pytest.mark.parametrize("damage", ["byte", "field"])
def test_when_records_unreadable_then_failed_with_status_and_notice(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path, damage: str
) -> None:
    if damage == "byte":
        (project / "PLAN.md").write_bytes(_PLAN.encode() + b"\xff\xfe\n")
    else:
        rows = project / "verification.csv"
        rows.write_text(
            rows.read_text()
            + 'x,y,2026-11-21,R9,"'
            + "z" * 200_000
            + '",pass,acceptance\n'
        )
    _commit_all(project)
    sink = home / "notified.txt"
    notifier = home / "notify.sh"
    notifier.write_text(f'#!/bin/sh\nprintf "%s" "$1" > "{sink}"\n')
    notifier.chmod(0o755)
    done = _launch(
        home, fake_claude, project, "finished", "--budget-usd", "5", "--max-resumes", "0",
        "--notify", str(notifier),
    )  # fmt: skip
    assert (done.returncode, _status(home)["state"], sink.exists()) == (
        5,
        "failed",
        True,
    )


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
    done = _approve(home, project)
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
    _approve(home, outside)
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
    _approve(home, other)
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
    _approve(home, project)
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


def test_when_environment_built_then_tool_homes_sit_in_scratch_folder(
    tmp_path: pathlib.Path,
) -> None:
    sys.path.insert(0, str(_HERE))
    import launch  # noqa: PLC0415 - the script is imported only for its pure builders

    layout = launch.Layout(root=tmp_path, work=tmp_path / "work")
    environment = launch.build_environment(
        grant=None, layout=layout, source={}, usage_wait_hours=1.0
    )
    homes = (
        "GH_CONFIG_DIR",
        "PIP_CACHE_DIR",
        "PRE_COMMIT_HOME",
        "VIRTUALENV_OVERRIDE_APP_DATA",
    )
    assert all(
        pathlib.Path(environment[name]).is_relative_to(layout.work) for name in homes
    )


def _filesystem_on(system: str, tmp_path: pathlib.Path) -> dict[str, list[str]]:
    sys.path.insert(0, str(_HERE))
    import launch  # noqa: PLC0415 - the script is imported only for its pure builders

    profile = launch.build_profile(
        grant=None,
        layout=launch.Layout(root=tmp_path, work=tmp_path / "work"),
        local_binding=False,
        mode="dontAsk",
        plugins=[],
        project=tmp_path / "project",
        reads=[],
        system=system,
    )
    return profile["sandbox"]["filesystem"]


def test_when_profile_built_on_macos_then_other_sessions_temp_folders_and_volumes_denied(
    tmp_path: pathlib.Path,
) -> None:
    filesystem = _filesystem_on("darwin", tmp_path)
    sessions = {
        f"/private/tmp/claude-{os.getuid()}/-*",
        f"/tmp/claude-{os.getuid()}/-*",
    }
    assert (
        sessions <= set(filesystem["denyRead"]),
        sessions <= set(filesystem["denyWrite"]),
        "/Volumes" in filesystem["denyRead"],
    ) == (True, True, True)


def test_when_profile_built_on_linux_then_only_paths_linux_has_named(
    tmp_path: pathlib.Path,
) -> None:
    filesystem = _filesystem_on("linux", tmp_path)
    named = filesystem["denyRead"] + filesystem["denyWrite"]
    macos_only = [p for p in named if p.startswith(("/private/tmp", "/Volumes"))]
    assert (macos_only, f"/tmp/claude-{os.getuid()}/-*" in filesystem["denyWrite"]) == (
        [],
        True,
    )


def test_when_environment_built_then_claude_code_does_not_update_mid_run(
    tmp_path: pathlib.Path,
) -> None:
    sys.path.insert(0, str(_HERE))
    import launch  # noqa: PLC0415 - the script is imported only for its pure builders

    layout = launch.Layout(root=tmp_path, work=tmp_path / "work")
    environment = launch.build_environment(
        grant=None, layout=layout, source={}, usage_wait_hours=1.0
    )
    assert environment["DISABLE_AUTOUPDATER"] == "1"


@pytest.mark.parametrize("shared", ["/dev/shm/bin", "/var/tmp/bin"])
def test_when_path_holds_a_shared_temp_folder_then_refused(
    tmp_path: pathlib.Path, shared: str
) -> None:
    sys.path.insert(0, str(_HERE))
    import launch  # noqa: PLC0415 - the script is imported only for its pure builders

    found = launch.check_path(f"{shared}:/usr/bin", forbidden=[tmp_path])
    assert found == [
        f"PATH entry {shared} is a folder the run can write or a temp folder"
    ]


def test_when_environment_built_then_pip_trusts_its_own_bundle(
    tmp_path: pathlib.Path,
) -> None:
    sys.path.insert(0, str(_HERE))
    import launch  # noqa: PLC0415 - the script is imported only for its pure builders

    layout = launch.Layout(root=tmp_path, work=tmp_path / "work")
    environment = launch.build_environment(
        grant=None, layout=layout, source={}, usage_wait_hours=1.0
    )
    assert environment["PIP_USE_DEPRECATED"] == "legacy-certs"


_HOOKS_CONFIG = """\
repos:
  - repo: local
    hooks:
      - id: say
        name: say
        entry: "true"
        language: system
  - repo: {remote}
    rev: {rev}
    hooks:
      - id: say
"""


def _hook_repository(folder: pathlib.Path) -> str:
    folder.mkdir()
    (folder / ".pre-commit-hooks.yaml").write_text(
        "- id: say\n  name: say\n  entry: 'true'\n  language: system\n"
    )
    _commit_all(folder)
    return _head(folder)


@pytest.mark.parametrize(
    "remote", ["local-path", "https://hooks.example.invalid/hooks"]
)
def test_when_project_names_hook_repositories_then_launcher_fetches_and_builds_nothing(
    home: pathlib.Path,
    fake_claude: pathlib.Path,
    project: pathlib.Path,
    grant: pathlib.Path,
    tmp_path: pathlib.Path,
    remote: str,
) -> None:
    hooks = tmp_path / "hooks"
    rev = _hook_repository(hooks)
    where = str(hooks) if remote == "local-path" else remote
    (project / ".pre-commit-config.yaml").write_text(
        _HOOKS_CONFIG.format(remote=where, rev=rev)
    )
    _commit_all(project)
    _approve(home, project)
    done = _launch(home, fake_claude, project, "blocked")
    stores = list((home / "runs").glob("*/work/pre-commit"))
    assert (stores, where in done.stderr) == ([], False)


def test_when_grant_names_code_host_then_run_may_reach_it(
    home: pathlib.Path,
    fake_claude: pathlib.Path,
    project: pathlib.Path,
    grant: pathlib.Path,
) -> None:
    grant.write_text(
        grant.read_text().replace('"secrets"', '"network": ["github.com"], "secrets"')
    )
    _approve(home, project)
    _launch(home, fake_claude, project, "finished")
    assert "github.com" in _profile(home)["sandbox"]["network"]["allowedDomains"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q", *sys.argv[1:]]))
