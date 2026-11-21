# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest"]
# ///
"""Tests for launch.py, run with ``uv run --script test_launch.py``.

A fake ``claude`` stands in for the real one: each invocation takes the next outcome from
a scenario file, appends a priced response to the session's transcript under a throwaway
home, and prints the stream-json result Claude Code 2.1.330 prints, or nothing for a drop.
"""

import json
import os
import pathlib
import subprocess
import sys
import textwrap

import pytest

_HERE = pathlib.Path(__file__).resolve().parent

_FAKE = textwrap.dedent(
    """\
    import json, os, pathlib, sys, time
    home = pathlib.Path(os.environ["HOME"])
    log = home / "calls.jsonl"
    with log.open("a") as out:
        out.write(json.dumps({"argv": sys.argv[1:], "env": sorted(os.environ)}) + "\\n")
    scenario = home / "scenario.txt"
    outcomes = scenario.read_text().split()
    outcome, rest = outcomes[0], outcomes[1:]
    scenario.write_text(" ".join(rest))
    session = sys.argv[sys.argv.index("--session-id" if "--session-id" in sys.argv else "--resume") + 1]
    transcript = home / ".claude" / "projects" / "-fake" / f"{session}.jsonl"
    transcript.parent.mkdir(parents=True, exist_ok=True)

    def spend(dollars, n):
        record = {"type": "assistant", "timestamp": "2026-11-21T10:00:00Z",
                  "message": {"id": f"{session}-{n}-{time.time_ns()}", "model": "claude-opus-5-5",
                              "usage": {"input_tokens": int(dollars * 250_000)}}}
        with transcript.open("a") as out:
            out.write(json.dumps(record) + "\\n")

    def result(subtype, text="", turns=3):
        print(json.dumps({"type": "result", "subtype": subtype, "result": text,
                          "num_turns": turns, "total_cost_usd": 0.10, "session_id": session}))

    if outcome == "spin_stream":
        for n in range(200):
            record = {"type": "assistant", "message": {"id": f"s-{n}", "model": "claude-opus-5-5",
                      "usage": {"input_tokens": 25_000}}}
            print(json.dumps(record), flush=True)
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
    else:
        result(outcome)
    """
)


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
    folder = tmp_path / "project"
    folder.mkdir()
    (folder / "prompt.md").write_text("Build the thing.\n")
    return folder


def _launch(
    home: pathlib.Path,
    fake_claude: pathlib.Path,
    project: pathlib.Path,
    scenario: str,
    *extra: str,
    environment: dict[str, str] | None = None,
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
            str(home / "plugin"),
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


def _calls(home: pathlib.Path) -> list[dict[str, list[str]]]:
    return [
        json.loads(line) for line in (home / "calls.jsonl").read_text().splitlines()
    ]


def _argument(argv: list[str], flag: str) -> str:
    return argv[argv.index(flag) + 1]


def test_when_run_finishes_then_exit_zero(
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
    profile = json.loads(
        pathlib.Path(_argument(_calls(home)[0]["argv"], "--settings")).read_text()
    )
    assert (
        profile["sandbox"]["enabled"],
        profile["sandbox"]["allowUnsandboxedCommands"],
        profile["disableClaudeAiConnectors"],
        profile["sandbox"]["filesystem"]["denyRead"][0],
    ) == (True, False, True, "~/")


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


def test_when_transcript_passes_budget_then_run_stopped(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    done = _launch(home, fake_claude, project, "spin", "--budget-usd", "1")
    status = json.loads(next((home / "runs").glob("*/status.json")).read_text())
    assert (done.returncode, status["detail"]) == (4, "the spend limit was reached")


def test_when_transcript_passes_turns_then_run_stopped(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path
) -> None:
    done = _launch(
        home, fake_claude, project, "spin", "--budget-usd", "100", "--max-turns", "10"
    )
    status = json.loads(next((home / "runs").glob("*/status.json")).read_text())
    assert (done.returncode, status["detail"]) == (4, "the turn limit was reached")


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


def _approve(home: pathlib.Path, project: pathlib.Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_HERE / "launch.py"), "--approve-grant", "--project", str(project)],
        capture_output=True,
        check=False,
        env={"HOME": str(home), "PATH": os.environ["PATH"]},
        text=True,
        timeout=60,
    )


def _write_grant(project: pathlib.Path) -> pathlib.Path:
    path = project / "grant.json"
    path.write_text(
        json.dumps(
            {
                "expires_on": "2999-01-01",
                "given_by": "owner",
                "given_on": "2026-11-21",
                "run": {"budget_usd": 1.5, "max_turns": 40},
                "secrets": ["PROJECT_TOKEN"],
            }
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


def test_when_project_grant_not_approved_then_refused(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path, unapproved: pathlib.Path
) -> None:
    done = _launch(home, fake_claude, project, "finished", "--budget-usd", "5")
    assert (done.returncode, "not approved" in done.stderr) == (1, True)


def test_when_project_grant_changed_after_approval_then_refused(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path, grant: pathlib.Path
) -> None:
    grant.write_text(grant.read_text().replace('"secrets"', '"network": ["evil.example"], "secrets"'))
    done = _launch(home, fake_claude, project, "finished", "--budget-usd", "5")
    assert (done.returncode, "not approved" in done.stderr) == (1, True)


def test_when_run_starts_then_file_tools_scoped_and_grant_and_plugins_denied(
    home: pathlib.Path, fake_claude: pathlib.Path, project: pathlib.Path, grant: pathlib.Path
) -> None:
    _launch(home, fake_claude, project, "finished", "--budget-usd", "5")
    profile = json.loads(pathlib.Path(_argument(_calls(home)[0]["argv"], "--settings")).read_text())
    allow, deny = profile["permissions"]["allow"], profile["permissions"]["deny"]
    deny_write = profile["sandbox"]["filesystem"]["denyWrite"]
    assert (
        {"Edit", "Write", "NotebookEdit"} & set(allow),
        f"Edit(/{project}/**)" in allow,
        "Edit(~/.claude/**)" in deny,
        f"Edit(/{project}/grant.json)" in deny,
        f"Edit(/{home / 'plugin'}/**)" in deny,
        str(project / "grant.json") in deny_write,
        str(home / "plugin") in deny_write,
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
    raise SystemExit(pytest.main([__file__, "-q"]))
