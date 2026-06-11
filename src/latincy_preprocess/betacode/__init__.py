"""
Beta Code → Unicode submodule.

Converts TLG/Perseus-style Beta Code for Ancient Greek into polytonic Unicode
(NFC). See :mod:`latincy_preprocess.betacode._rules` for attribution and the
transliteration caveat.

Basic usage:
    >>> from latincy_preprocess.betacode import beta_to_unicode
    >>> beta_to_unicode("a)/nqrwpos")
    'ἄνθρωπος'
"""

from latincy_preprocess.betacode._rules import (
    BETA_REORDER,
    BETA_REPLACE,
    BetaCodeReplacer,
    beta_to_unicode,
    is_betacode,
)

__all__ = [
    "BetaCodeReplacer",
    "beta_to_unicode",
    "is_betacode",
    "BETA_REPLACE",
    "BETA_REORDER",
]
