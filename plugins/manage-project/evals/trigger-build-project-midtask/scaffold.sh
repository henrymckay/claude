#!/bin/sh
# Lay out a tiny planned project with its first milestone built, in the case's workspace.
set -eu

mkdir -p src/wordcount tests

cat > PLAN.md <<'EOF'
# wordcount

A command-line tool that counts the words in a text file.

## Brief

### Requirements

- **R1** Print the number of words in a file.
- **R2** Print the N most common words with `--top N`.

## Delivery

### Milestones

- [x] **M1 Count** — R1; done when `wordcount sample.txt` prints the count.
- [ ] **M2 Top words** — R2; done when `wordcount --top 3 sample.txt` prints three words with their counts.
EOF

cat > pyproject.toml <<'EOF'
[project]
name = "wordcount"
version = "0.1.0"
requires-python = ">=3.13"

[project.scripts]
wordcount = "wordcount.cli:main"
EOF

cat > src/wordcount/__init__.py <<'EOF'
EOF

cat > src/wordcount/core.py <<'EOF'
"""Count words in text."""


def count_words(text: str) -> int:
    """Return the number of whitespace-separated words in ``text``."""
    return len(text.split())
EOF

cat > src/wordcount/cli.py <<'EOF'
"""Command line for wordcount."""

import pathlib
import sys

from wordcount import core


def main() -> None:
    """Print the word count of the file named on the command line."""
    print(core.count_words(pathlib.Path(sys.argv[1]).read_text()))
EOF

cat > tests/test_core.py <<'EOF'
from wordcount import core


def test_count_words_given_two_words_returns_two() -> None:
    assert core.count_words("hello world") == 2
EOF

git init -q
git add PLAN.md pyproject.toml src tests
git -c user.name=eval -c user.email=eval@example.invalid commit -q -m "feat: count words (M1)"
