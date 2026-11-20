# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Total a Claude Code session's tokens and list-price dollars per stage and model."""

import argparse
import collections
import collections.abc
import csv
import dataclasses
import datetime
import decimal
import json
import pathlib
import re
import sys
import typing

_CACHE_WRITE_1H: typing.Final = decimal.Decimal(2)
_CACHE_WRITE_5M: typing.Final = decimal.Decimal("1.25")
_COLUMNS: typing.Final[tuple[str, ...]] = (
    "agents",
    "cache_read",
    "cache_write",
    "dollars",
    "effort",
    "input",
    "model",
    "output",
    "session",
    "stage",
    "started",
    "wall_minutes",
)
_FAST: typing.Final = decimal.Decimal(2)
_MILLION: typing.Final = decimal.Decimal(1_000_000)
_SESSION: typing.Final = "session"


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class _Message:
    agent: str
    cache_read: int
    cache_write_1h: int
    cache_write_5m: int
    effort: str
    fast: bool
    input: int
    model: str
    output: int


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class _Price:
    cache_read: decimal.Decimal
    input: decimal.Decimal
    output: decimal.Decimal


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class _Transcript:
    agent: str
    label: str
    messages: tuple[_Message, ...]
    parent: str
    times: tuple[datetime.datetime, ...]


def _describe_efforts(efforts: collections.Counter[str]) -> str:
    """Return the efforts a row's responses ran at, a mixed row showing each.

    A skill's frontmatter changes the turn's effort from the moment it loads, so
    a stage can run partly at another effort than it was handed; naming only
    the most common value would hide that.

    :param efforts: How many responses ran at each effort.
    :returns: The one effort, or each as ``effort:count``, most common first,
        joined by ``/``; empty where no response recorded one.
    """
    if len(efforts) <= 1:
        return next(iter(efforts), "")
    return "/".join(f"{effort}:{count}" for effort, count in efforts.most_common())


def _find_root(agent: str, *, parents: collections.abc.Mapping[str, str]) -> str:
    """Return the top-level subagent a nested one was spawned under.

    :param agent: The subagent's id, or the empty id of the session itself.
    :param parents: Each subagent's parent, empty for one the session spawned.
    :returns: The id of the stage the subagent belongs to.
    """
    seen = {agent}
    while parents.get(agent, "") and parents[agent] not in seen:
        agent = parents[agent]
        seen.add(agent)
    return agent


def _find_transcript(cwd: pathlib.Path) -> pathlib.Path | None:
    """Return the newest session transcript Claude Code keeps for a directory.

    :param cwd: The directory the session ran in.
    :returns: The transcript, or None where the directory has none.
    """
    folder = (
        pathlib.Path.home()
        / ".claude"
        / "projects"
        / re.sub(r"[^A-Za-z0-9]", "-", str(cwd))
    )
    return max(
        folder.glob("*.jsonl"), key=lambda file: file.stat().st_mtime, default=None
    )


def _is_under(
    agent: str, *, ancestor: str, parents: collections.abc.Mapping[str, str]
) -> bool:
    """Return whether a subagent is the ancestor or was spawned beneath it.

    :param agent: The subagent's id.
    :param ancestor: The id of the subagent whose stage is wanted.
    :param parents: Each subagent's parent, empty for one the session spawned.
    :returns: True where the ancestor is the subagent or one of its parents.
    """
    seen: set[str] = set()
    while agent and agent not in seen:
        if agent == ancestor:
            return True
        seen.add(agent)
        agent = parents.get(agent, "")
    return False


def _parse_message(
    message: collections.abc.Mapping[str, typing.Any], *, agent: str, effort: str
) -> _Message:
    """Return the token counts of one response.

    :param message: The record's ``message``, holding ``model`` and ``usage``.
    :param agent: The id of the subagent that sent it, empty for the session.
    :param effort: The effort the record says the response ran at.
    :returns: The response's counts.
    """
    usage = message.get("usage") or {}
    written = usage.get("cache_creation") or {}
    write_1h = written.get("ephemeral_1h_input_tokens", 0)
    return _Message(
        agent=agent,
        cache_read=usage.get("cache_read_input_tokens", 0),
        cache_write_1h=write_1h,
        cache_write_5m=written.get(
            "ephemeral_5m_input_tokens",
            usage.get("cache_creation_input_tokens", 0) - write_1h,
        ),
        effort=effort,
        fast=usage.get("speed") == "fast",
        input=usage.get("input_tokens", 0),
        model=str(message.get("model", "")),
        output=usage.get("output_tokens", 0),
    )


def _price_message(
    message: _Message, *, prices: collections.abc.Mapping[str, _Price]
) -> decimal.Decimal | None:
    """Return a response's list-price dollars.

    The family is matched within the model's name, so an older model of a
    family is priced at the current one's rates.

    :param message: The response's counts.
    :param prices: List prices per million tokens by model family.
    :returns: The dollars, or None for a model with no price.
    """
    family = next((name for name in prices if name in message.model), None)
    if family is None:
        return None
    price = prices[family]
    paid = (
        message.input * price.input
        + message.output * price.output
        + message.cache_read * price.cache_read
        + message.cache_write_5m * price.input * _CACHE_WRITE_5M
        + message.cache_write_1h * price.input * _CACHE_WRITE_1H
    )
    return paid * (_FAST if message.fast else 1) / _MILLION


def _prices() -> dict[str, _Price]:
    """Return list prices per million tokens by model family.

    Read from platform.claude.com/docs/en/about-claude/pricing on 2026-11-18,
    Haiku at its rate for prompts to 100k tokens; change them with the table in
    choose-model's Know the prices.

    :returns: The prices by family name.
    """
    return {
        "fable": _Price(
            cache_read=decimal.Decimal("0.20"),
            input=decimal.Decimal(8),
            output=decimal.Decimal(40),
        ),
        "haiku": _Price(
            cache_read=decimal.Decimal("0.01"),
            input=decimal.Decimal("0.10"),
            output=decimal.Decimal("0.50"),
        ),
        "opus": _Price(
            cache_read=decimal.Decimal("0.20"),
            input=decimal.Decimal(4),
            output=decimal.Decimal(20),
        ),
        "sonnet": _Price(
            cache_read=decimal.Decimal("0.10"),
            input=decimal.Decimal(2),
            output=decimal.Decimal(10),
        ),
    }


def _read_meta(path: pathlib.Path) -> dict[str, typing.Any]:
    """Return a subagent's metadata.

    :param path: The ``.meta.json`` beside the subagent's transcript.
    :returns: Its fields, or none where the file is absent.
    """
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _read_session(path: pathlib.Path) -> tuple[_Transcript, ...]:
    """Return the session's own transcript and each subagent's.

    :param path: The session's transcript, the ``.jsonl`` beside its folder.
    :returns: The session's transcript first, then each subagent's.
    """
    subagents = tuple(
        _read_transcript(
            file,
            agent=file.stem.removeprefix("agent-"),
            label=str(meta.get("description", "")),
            parent=str(meta.get("parentAgentId", "")).removeprefix("agent-"),
        )
        for file in sorted((path.with_suffix("") / "subagents").glob("agent-*.jsonl"))
        for meta in (_read_meta(file.with_suffix(".meta.json")),)
    )
    return (_read_transcript(path, agent="", label=_SESSION, parent=""), *subagents)


def _read_transcript(
    path: pathlib.Path, *, agent: str, label: str, parent: str
) -> _Transcript:
    """Return one transcript file's billed responses, each counted once.

    A response is written as one record per content block, each repeating its
    usage, so records are keyed by the response's id and the last one kept.

    :param path: The transcript file.
    :param agent: The subagent's id, empty for the session's own file.
    :param label: The stage's name: the subagent's description, or "session".
    :param parent: The id of the subagent that spawned it, if any.
    :returns: Its responses and the times of all its records.
    """
    by_id: dict[str, _Message] = {}
    times: list[datetime.datetime] = []
    with path.open(encoding="utf-8") as lines:
        for line in lines:
            record = json.loads(line)
            stamp = record.get("timestamp")
            if isinstance(stamp, str):
                times.append(datetime.datetime.fromisoformat(stamp))
            message = record.get("message")
            if (
                record.get("type") == "assistant"
                and isinstance(message, dict)
                and message.get("model") != "<synthetic>"
            ):
                by_id[message.get("id") or record.get("uuid")] = _parse_message(
                    message, agent=agent, effort=str(record.get("effort", ""))
                )
    return _Transcript(
        agent=agent,
        label=label,
        messages=tuple(by_id.values()),
        parent=parent,
        times=tuple(times),
    )


def _total_stage(
    transcripts: collections.abc.Sequence[_Transcript],
    *,
    label: str,
    prices: collections.abc.Mapping[str, _Price],
    session: str,
) -> list[dict[str, str]]:
    """Return one row per model for a stage's transcripts.

    :param transcripts: The stage's subagent and every subagent beneath it.
    :param label: The stage's name.
    :param prices: List prices per million tokens by model family.
    :param session: The session's id.
    :returns: The stage's rows, ``agents`` counting the subagents that ran on
        each row's model, so the column sums across rows.
    """
    times = sorted(stamp for transcript in transcripts for stamp in transcript.times)
    by_model: dict[str, list[_Message]] = collections.defaultdict(list)
    for transcript in transcripts:
        for message in transcript.messages:
            by_model[message.model].append(message)
    rows = []
    for model, messages in sorted(by_model.items()):
        priced = [_price_message(message, prices=prices) for message in messages]
        known = [dollars for dollars in priced if dollars is not None]
        efforts = collections.Counter(
            message.effort for message in messages if message.effort
        )
        rows.append(
            {
                "agents": str(len({m.agent for m in messages if m.agent})),
                "cache_read": str(sum(message.cache_read for message in messages)),
                "cache_write": str(
                    sum(m.cache_write_5m + m.cache_write_1h for m in messages)
                ),
                "dollars": ""
                if len(known) < len(priced)
                else f"{sum(known, decimal.Decimal(0)):.2f}",
                "effort": _describe_efforts(efforts),
                "input": str(sum(message.input for message in messages)),
                "model": model,
                "output": str(sum(message.output for message in messages)),
                "session": session,
                "stage": label,
                "started": times[0]
                .astimezone(datetime.UTC)
                .isoformat(timespec="seconds"),
                "wall_minutes": f"{(times[-1] - times[0]).total_seconds() / 60:.1f}",
            }
        )
    return rows


def main() -> None:
    """Print the ledger rows as CSV on standard output."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "transcript",
        nargs="?",
        type=pathlib.Path,
        help="session .jsonl; default: the newest for this directory",
    )
    parser.add_argument(
        "--agent",
        default="",
        help="a subagent's id, or 'session': total only it and those beneath it",
    )
    parser.add_argument(
        "--no-header",
        action="store_true",
        help="omit the header, to append to a ledger",
    )
    parser.add_argument(
        "--stage", default="", help="with --agent, the stage's name, e.g. M2"
    )
    arguments = parser.parse_args()
    path = arguments.transcript or _find_transcript(pathlib.Path.cwd())
    if path is None:
        raise SystemExit("no session transcript for this directory")
    rows = total_session(path, agent=arguments.agent, stage=arguments.stage)
    if not rows:
        raise SystemExit(f"no messages for agent {arguments.agent!r} in {path}")
    writer = csv.DictWriter[str](sys.stdout, fieldnames=_COLUMNS, lineterminator="\n")
    if not arguments.no_header:
        writer.writeheader()
    writer.writerows(rows)


def total_session(
    path: pathlib.Path, *, agent: str = "", stage: str = ""
) -> list[dict[str, str]]:
    """Return the ledger rows for a session, or for one subagent's stage.

    :param path: The session's transcript, the ``.jsonl`` beside its folder.
    :param agent: A subagent's id, to total it and every subagent beneath it,
        or ``session`` for the session's own responses.
    :param stage: With ``agent``, the stage's name in place of its description.
    :returns: One row per stage and model, nested subagents in their stage,
        in the order the stages started.
    """
    transcripts = [transcript for transcript in _read_session(path) if transcript.times]
    parents = {transcript.agent: transcript.parent for transcript in transcripts}
    labels = {transcript.agent: transcript.label for transcript in transcripts}
    wanted = agent.removeprefix("agent-")
    if wanted == _SESSION:
        stages = {"": [t for t in transcripts if not t.agent]}
    elif wanted:
        stages = {
            wanted: [
                t
                for t in transcripts
                if _is_under(t.agent, ancestor=wanted, parents=parents)
            ]
        }
    else:
        stages = collections.defaultdict(list)
        for transcript in transcripts:
            stages[_find_root(transcript.agent, parents=parents)].append(transcript)
    rows = [
        row
        for root, members in stages.items()
        if members
        for row in _total_stage(
            members,
            label=stage if wanted and stage else labels.get(root, root),
            prices=_prices(),
            session=path.stem,
        )
    ]
    return sorted(rows, key=lambda row: row["started"])


if __name__ == "__main__":
    main()
