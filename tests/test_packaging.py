"""Packaging invariants.

The version number lives in exactly one place — ``[project].version`` in
pyproject.toml — and everything else derives from it. It has drifted three
times (0.4.0, 0.5.0, 0.5.1), each time producing a wheel whose ``pip show``
version and ``latincy_preprocess.__version__`` disagreed, and each time it was
caught by hand during a pre-publish audit rather than by CI. These tests make
that class of defect fail the build instead.
"""

from pathlib import Path

import pytest

import latincy_preprocess

try:  # stdlib on 3.11+; CI's 3.11-3.14 legs carry the check
    import tomllib
except ImportError:  # pragma: no cover - 3.10 only
    tomllib = None

PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def _pyproject_version() -> str:
    with PYPROJECT.open("rb") as fh:
        return tomllib.load(fh)["project"]["version"]


@pytest.mark.skipif(tomllib is None, reason="needs stdlib tomllib (3.11+)")
@pytest.mark.skipif(not PYPROJECT.exists(), reason="not running from a source tree")
def test_dunder_version_matches_pyproject():
    """__version__ must equal pyproject.toml's [project].version.

    Guards the exact defect that shipped three releases running: the literal in
    __init__.py was bumped independently of pyproject.toml, or not at all.
    """
    assert latincy_preprocess.__version__ == _pyproject_version()


def test_dunder_version_is_not_the_uninstalled_sentinel():
    """The test suite must run against an installed distribution.

    __init__.py falls back to 0.0.0.dev0 when importlib.metadata finds no
    installed distribution. If that fallback is what tests see, the version
    check above is comparing against a placeholder and proves nothing.
    """
    assert latincy_preprocess.__version__ != "0.0.0.dev0", (
        "latincy_preprocess is importable but not installed — "
        "run `pip install -e .` (or `maturin develop`) before testing"
    )
