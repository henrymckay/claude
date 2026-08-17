"""Lint the Python examples embedded in the skills.

An example is code, so it is held to the conventions the skills themselves
mandate (see write-markdown). Only the rules a formatter cannot fix are
checked: a fenced block is a fragment, so it legitimately omits imports,
shows them in a teaching order, and runs a few columns long for readability.
"""

import dataclasses
import pathlib
import re
import subprocess
import sys
import tempfile

_FENCE = re.compile(r"^```python\s*$")
_FINDING = re.compile(r"^(?:.*/)?(?P<name>[^/:]+)\.py:(?P<line>\d+):(?P<rest>.*)$")
_IGNORE = "D100,C414"
_SELECT = "D,N,UP,B,SIM,C4"


@dataclasses.dataclass(frozen=True, slots=True)
class _Block:
    """Where an extracted example came from."""

    path: pathlib.Path
    fence: int


def main(arguments: list[str]) -> int:
    """Extract every Python block from the given Markdown files and lint it.

    :param arguments: Paths of the Markdown files to check.
    :returns: The exit status to leave with.
    """
    with tempfile.TemporaryDirectory() as directory:
        blocks = {
            name: block
            for path in arguments
            for name, block in _extracted(pathlib.Path(path), pathlib.Path(directory))
        }
        if not blocks:
            return 0
        return _reported(_checked(pathlib.Path(directory)), blocks)


def _checked(directory: pathlib.Path) -> subprocess.CompletedProcess[str]:
    """Run ruff over the extracted blocks, isolated from any ambient config.

    :raises SystemExit: If ruff is not on the path, which pre-commit provides.
    """
    try:
        return subprocess.run(
            [
                "ruff",
                "check",
                "--isolated",
                "--no-cache",
                "--output-format",
                "concise",
                "--select",
                _SELECT,
                "--ignore",
                _IGNORE,
                "--config",
                'lint.pydocstyle.convention = "pep257"',
                str(directory),
            ],
            capture_output=True,
            check=False,
            text=True,
        )
    except FileNotFoundError:
        raise SystemExit(
            "ruff is not on the path; run this through pre-commit, or install ruff."
        ) from None


def _extracted(path: pathlib.Path, directory: pathlib.Path) -> list[tuple[str, _Block]]:
    """Write each fenced Python block to its own file, named for where it came from."""
    written = []
    inside, fence, lines = False, 0, []
    for number, line in enumerate(path.read_text().splitlines(), start=1):
        if not inside and _FENCE.match(line):
            inside, fence, lines = True, number, []
        elif inside and line.strip() == "```":
            name = f"{path.as_posix().replace('/', '__').removesuffix('.md')}__L{fence}"
            directory.joinpath(f"{name}.py").write_text("\n".join(lines) + "\n")
            written.append((name, _Block(path=path, fence=fence)))
            inside = False
        elif inside:
            lines.append(line)
    return written


def _reported(
    checked: subprocess.CompletedProcess[str],
    blocks: dict[str, _Block],
) -> int:
    """Print ruff's findings against the Markdown line they actually sit on."""
    if checked.returncode == 0:
        return 0
    for finding in checked.stdout.splitlines():
        sys.stdout.write(f"{_located(finding, blocks)}\n")
    sys.stderr.write(checked.stderr)
    return 1


def _located(finding: str, blocks: dict[str, _Block]) -> str:
    """Rewrite one finding's temporary path as the Markdown file and line."""
    match = _FINDING.match(finding)
    if match is None or match.group("name") not in blocks:
        return finding
    block = blocks[match.group("name")]
    return (
        f"{block.path}:{block.fence + int(match.group('line'))}:{match.group('rest')}"
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
