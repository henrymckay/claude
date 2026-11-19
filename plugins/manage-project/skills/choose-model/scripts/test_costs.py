# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest"]
# ///
"""Tests for costs.py, run with ``uv run --script test_costs.py``."""

import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent))

import costs


def _response(
    identity: str, *, model: str, output: int, stamp: str, speed: str = "standard"
) -> dict[str, object]:
    return {
        "effort": "medium",
        "message": {
            "id": identity,
            "model": model,
            "usage": {
                "cache_creation": {
                    "ephemeral_1h_input_tokens": 0,
                    "ephemeral_5m_input_tokens": 1_000_000,
                },
                "cache_creation_input_tokens": 1_000_000,
                "cache_read_input_tokens": 1_000_000,
                "input_tokens": 1_000_000,
                "output_tokens": output,
                "speed": speed,
            },
        },
        "timestamp": stamp,
        "type": "assistant",
    }


def _write(path: pathlib.Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records))


@pytest.fixture
def session(tmp_path: pathlib.Path) -> pathlib.Path:
    main = tmp_path / "s1.jsonl"
    opus = "claude-opus-5-5"
    sonnet = "claude-sonnet-5-5"
    _write(
        main,
        [
            _response("r1", model=opus, output=0, stamp="2026-11-19T10:00:00Z"),
            _response("r1", model=opus, output=0, stamp="2026-11-19T10:00:01Z"),
        ],
    )
    folder = tmp_path / "s1" / "subagents"
    _write(
        folder / "agent-m2.jsonl",
        [_response("r2", model=sonnet, output=0, stamp="2026-11-19T10:01:00Z")],
    )
    (folder / "agent-m2.meta.json").write_text(json.dumps({"description": "Build M2"}))
    _write(
        folder / "agent-ev.jsonl",
        [
            _response(
                "r3",
                model=sonnet,
                output=1_000_000,
                stamp="2026-11-19T10:31:00Z",
                speed="fast",
            )
        ],
    )
    (folder / "agent-ev.meta.json").write_text(
        json.dumps({"description": "Evaluate M2", "parentAgentId": "m2"})
    )
    return main


def test_when_session_totalled_then_repeated_response_counted_once(
    session: pathlib.Path,
) -> None:
    rows = costs.total_session(session, agent="session")
    assert [(row["input"], row["dollars"]) for row in rows] == [("1000000", "9.20")]


def test_when_stage_totalled_then_nested_subagent_counted_in_it(
    session: pathlib.Path,
) -> None:
    rows = costs.total_session(session, agent="m2", stage="M2")
    assert [
        (row["stage"], row["agents"], row["dollars"], row["wall_minutes"])
        for row in rows
    ] == [("M2", "2", "33.80", "30.0")]


def test_when_nested_subagent_selected_then_only_it_totalled(
    session: pathlib.Path,
) -> None:
    rows = costs.total_session(session, agent="agent-ev")
    assert [(row["stage"], row["dollars"]) for row in rows] == [
        ("Evaluate M2", "29.20")
    ]


def test_when_unknown_agent_selected_then_no_rows(session: pathlib.Path) -> None:
    assert costs.total_session(session, agent="missing") == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
