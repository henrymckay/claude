"""Read a project's standing grant: what the owner approved ahead of a run.

Runs under any Python from 3.9, since the guard hook that imports it runs under whatever
``python3`` the machine has; its records are named tuples, since ``dataclasses`` imports
``inspect``, which costs the hook about 120 ms on every tool call under Python 3.9.
"""

from __future__ import annotations

import datetime
import json
import os
import pathlib
import re
import typing
import urllib.parse

FILE_NAME: typing.Final = "grant.json"
_ENV_FILE: typing.Final = "CLAUDE_GRANT_FILE"
_MAX_BYTES: typing.Final = 64 * 1024
_REQUIRED: typing.Final = ("expires_on", "given_by", "given_on")
_SCP: typing.Final = re.compile(r"^(?:[^@/:]+@)?([^@/:]+):(?!//)(.+)$")


class GrantError(Exception):
    """A grant file that is missing a field, malformed or expired."""


class Account(typing.NamedTuple):
    """One account the grant lets a run act on."""

    account: str
    actions: tuple[str, ...]
    provider: str
    spend_limit_usd: float
    tier: str


class Grant(typing.NamedTuple):
    """What the owner approved in advance, read from ``grant.json``."""

    accounts: tuple[Account, ...]
    budget_usd: float | None
    expires_on: datetime.date
    given_by: str
    given_on: datetime.date
    max_turns: int | None
    network: tuple[str, ...]
    path: pathlib.Path
    remotes: tuple[str, ...]
    secrets: tuple[str, ...]
    web: str


def _read_date(value: object, *, field: str) -> datetime.date:
    """Return an ISO date field.

    :param value: The field's raw value.
    :param field: The field's name, for the error.
    :returns: The date.
    :raises GrantError: If it is not an ISO date.
    """
    try:
        return datetime.date.fromisoformat(str(value))
    except ValueError as failure:
        raise GrantError(f"{field} is not an ISO date: {value!r}") from failure


def _read_strings(value: object, *, field: str) -> tuple[str, ...]:
    """Return a list-of-strings field.

    :param value: The field's raw value, absent as None.
    :param field: The field's name, for the error.
    :returns: The strings, empty where the field is absent.
    :raises GrantError: If it is not a list of strings.
    """
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise GrantError(f"{field} must be a list of strings")
    return tuple(value)


def _read_number(value: object, *, field: str) -> float | None:
    """Return a non-negative number field.

    :param value: The field's raw value, absent as None.
    :param field: The field's name, for the error.
    :returns: The number, or None where absent.
    :raises GrantError: If it is not a non-negative number.
    """
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise GrantError(f"{field} must be a non-negative number")
    return float(value)


def find_grant(project: pathlib.Path) -> pathlib.Path | None:
    """Return the grant file that governs a project, if there is one.

    A launcher's snapshot, named by ``CLAUDE_GRANT_FILE``, wins over the project's own
    file, so a run that edits ``grant.json`` cannot widen what it was given.

    :param project: The project's root folder.
    :returns: The grant file, or None where neither exists.
    """
    named = os.environ.get(_ENV_FILE, "")
    if named:
        return pathlib.Path(named)
    candidate = project / FILE_NAME
    return candidate if candidate.is_file() else None


def remote_key(url: str, *, bare_is_host: bool) -> str | None:
    """Return a remote's host and path in one comparable form, or None for a doubtful one.

    The URL is parsed as git does, by its scheme or as ``user@host:path``, so a look-alike
    such as ``https://evil.example\\@github.com/owner/repo`` cannot borrow a trusted host:
    a backslash, a control character, a query, a fragment or a ``..`` segment makes the
    remote doubtful, and a doubtful remote matches nothing. ``git@github.com:Owner/Repo.git``,
    ``https://github.com/owner/repo/`` and ``ssh://git@github.com:22/owner/repo.git`` all
    give ``github.com/owner/repo``; a local path gives ``file:`` and the path.

    :param url: A remote URL in any form git accepts, or a grant's entry.
    :param bare_is_host: Read ``host/path`` with no scheme as a host and path, as a grant
        writes it, rather than as a relative local path, as git would.
    :returns: The key, lower case, with no scheme, user, port or ``.git``; or None.
    """
    text = url.strip(" ")
    if not text or "\\" in text or any(ord(c) < 32 or ord(c) == 127 for c in text):
        return None
    if "://" in text:
        try:
            parts = urllib.parse.urlsplit(text)
            port = parts.port
        except ValueError:
            return None
        del port
        if parts.query or parts.fragment or "?" in text or "#" in text:
            return None
        if parts.scheme.lower() == "file":
            return _path_key(parts.path)
        host, path = (parts.hostname or "").lower(), parts.path
    elif text.startswith("/"):
        return _path_key(text)
    elif (scp := _SCP.match(text)) and "/" not in scp.group(1):
        host, path = scp.group(1).lower(), scp.group(2)
    elif bare_is_host and "/" in text:
        host, _, path = text.partition("/")
        host = host.lower()
    else:
        return None
    if not re.fullmatch(r"[a-z0-9.-]+", host) or "?" in path or "#" in path:
        return None
    segments = [segment for segment in path.split("/") if segment]
    if not segments or any(segment in (".", "..") for segment in segments):
        return None
    joined = re.sub(r"\.git$", "", "/".join(segments))
    return f"{host}/{joined}".lower()


def _path_key(path: str) -> str | None:
    """Return the key of a local repository path.

    :param path: An absolute path.
    :returns: ``file:`` and the normalised path without ``.git``, or None if relative.
    """
    if not path.startswith("/"):
        return None
    return "file:" + re.sub(r"\.git/?$", "", os.path.normpath(path)).lower()


def _read_remotes(value: object) -> tuple[str, ...]:
    """Return the grant's push remotes as keys.

    :param value: The ``remotes`` field.
    :returns: Each remote's key.
    :raises GrantError: If one cannot be read as a remote, so the grant counts as none.
    """
    keys = tuple(
        remote_key(remote, bare_is_host=True)
        for remote in _read_strings(value, field="remotes")
    )
    if None in keys:
        raise GrantError(
            "remotes holds an entry that is not a plain host and path or URL"
        )
    return typing.cast("tuple[str, ...]", keys)


def read_grant(path: pathlib.Path, *, today: datetime.date | None = None) -> Grant:
    """Return a grant, refusing one that is malformed or past its expiry.

    :param path: The grant file.
    :param today: The date to check expiry against; the local date by default.
    :returns: The grant.
    :raises GrantError: If the file is unreadable, too large, missing a required
        field, malformed or expired.
    """
    try:
        raw = path.read_bytes()
    except OSError as failure:
        raise GrantError(f"cannot read {path}: {failure.strerror}") from failure
    if len(raw) > _MAX_BYTES:
        raise GrantError(f"{path} is larger than {_MAX_BYTES} bytes")
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as failure:
        raise GrantError(f"{path} is not JSON") from failure
    if not isinstance(data, dict):
        raise GrantError(f"{path} must hold a JSON object")
    missing = [field for field in _REQUIRED if not data.get(field)]
    if missing:
        raise GrantError(f"{path} lacks {', '.join(missing)}")
    expires_on = _read_date(data["expires_on"], field="expires_on")
    if expires_on < (today or datetime.date.today()):
        raise GrantError(f"{path} expired on {expires_on.isoformat()}")
    run = data.get("run") or {}
    if not isinstance(run, dict):
        raise GrantError("run must be an object")
    turns = _read_number(run.get("max_turns"), field="run.max_turns")
    accounts = data.get("accounts") or []
    if not isinstance(accounts, list) or not all(isinstance(a, dict) for a in accounts):
        raise GrantError("accounts must be a list of objects")
    web = str(data.get("web", "docs"))
    if web not in ("docs", "open", "off"):
        raise GrantError("web must be docs, open or off")
    return Grant(
        accounts=tuple(
            Account(
                account=str(entry.get("account", "")),
                actions=_read_strings(entry.get("actions"), field="accounts.actions"),
                provider=str(entry.get("provider", "")),
                spend_limit_usd=_read_number(
                    entry.get("spend_limit_usd", 0), field="accounts.spend_limit_usd"
                )
                or 0.0,
                tier=str(entry.get("tier", "")),
            )
            for entry in accounts
        ),
        budget_usd=_read_number(run.get("budget_usd"), field="run.budget_usd"),
        expires_on=expires_on,
        given_by=str(data["given_by"]),
        given_on=_read_date(data["given_on"], field="given_on"),
        max_turns=None if turns is None else int(turns),
        network=_read_strings(data.get("network"), field="network"),
        path=path,
        remotes=_read_remotes(data.get("remotes")),
        secrets=_read_strings(data.get("secrets"), field="secrets"),
        web=web,
    )
