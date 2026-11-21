# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest"]
# ///
"""Tests for grant.py, run with ``uv run --script test_grant.py``."""

import datetime
import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent))

import grant

_ALLOWED = "github.com/owner/repo"


@pytest.mark.parametrize(
    ("url", "key"),
    [
        ("https://github.com/owner/repo", _ALLOWED),
        ("HTTPS://GitHub.com/Owner/Repo.git/", _ALLOWED),
        ("ssh://git@github.com:22/owner/repo.git", _ALLOWED),
        ("https://user:pa:ss@github.com/owner/repo", _ALLOWED),
        ("git@github.com:owner/repo.git", _ALLOWED),
        ("https://github.com@evil.example/owner/repo", "evil.example/owner/repo"),
        ("https://evil.example\\@github.com/owner/repo", None),
        ("https://evil.example/#@github.com/owner/repo", None),
        ("https://github.com/owner/repo?x=1", None),
        ("https://github.com/owner/repo/../other", None),
        ("https://github.com/owner/repo\n", None),
        ("https://github.com:99999/owner/repo", None),
        ("/srv/git/repo.git", "file:/srv/git/repo"),
        ("github.com/owner/repo", None),
    ],
)
def test_when_git_url_keyed_then_host_and_path_as_git_reads_them(
    url: str, key: str | None
) -> None:
    assert grant.remote_key(url, bare_is_host=False) == key


def test_when_grant_entry_is_host_and_path_then_keyed_as_host() -> None:
    assert grant.remote_key(_ALLOWED, bare_is_host=True) == _ALLOWED


@pytest.fixture
def grant_file(tmp_path: pathlib.Path) -> pathlib.Path:
    path = tmp_path / "grant.json"
    path.write_text(
        json.dumps(
            {
                "expires_on": "2999-01-01",
                "given_by": "owner",
                "given_on": "2026-11-21",
                "remotes": ["https://evil.example\\@github.com/owner/repo"],
            }
        )
    )
    return path


def test_when_grant_names_doubtful_remote_then_grant_refused(
    grant_file: pathlib.Path,
) -> None:
    with pytest.raises(grant.GrantError):
        grant.read_grant(grant_file, today=datetime.date(2026, 11, 21))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
