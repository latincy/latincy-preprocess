"""
Ancient Greek normalization submodule.

Canonicalizes elision (all known apostrophe encodings -> U+2019), macron/breve
stripping, and accent folding for lookup-table matching. See
:mod:`latincy_preprocess.grc._rules` for the full standard and its rationale.
Requires the ``grc`` extra (``pip install latincy-preprocess[grc]``) for the
``greek-normalisation`` dependency this module is built on.

Basic usage:
    >>> from latincy_preprocess.grc import normalize_surface, normalize_norm
    >>> normalize_surface("μυρίʼ")
    'μυρί’'
    >>> normalize_norm("δʼ")
    'δέ'
"""

from latincy_preprocess.grc._rules import (
    GRAVE_TO_ACUTE,
    GRC_ELISION_EXTRA,
    is_greek_word,
    normalize_lookup_key,
    normalize_norm,
    normalize_surface,
)

__all__ = [
    "GRAVE_TO_ACUTE",
    "GRC_ELISION_EXTRA",
    "is_greek_word",
    "normalize_lookup_key",
    "normalize_norm",
    "normalize_surface",
]
