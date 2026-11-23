#!/bin/sh
# Lay out a tiny Python package with one function and its test, in the case's workspace.
set -eu

mkdir -p src/stats tests

cat > pyproject.toml <<'EOF'
[project]
name = "stats"
version = "0.1.0"
requires-python = ">=3.13"
EOF

cat > src/stats/__init__.py <<'EOF'
EOF

cat > src/stats/core.py <<'EOF'
"""Summary statistics over a sequence of numbers."""

from collections.abc import Sequence


def mean(values: Sequence[float]) -> float:
    """Return the arithmetic mean of ``values``, which must not be empty."""
    return sum(values) / len(values)
EOF

cat > tests/test_core.py <<'EOF'
from stats import core


def test_mean_given_three_values_returns_their_average() -> None:
    assert core.mean([1.0, 2.0, 6.0]) == 3.0
EOF
