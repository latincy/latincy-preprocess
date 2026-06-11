"""
Beta Code → Unicode conversion for Ancient Greek.

Converts TLG/Perseus-style Beta Code (Greek transliterated into ASCII with
``)`` ``(`` ``/`` ``\\`` ``=`` ``|`` diacritic markers) into polytonic Unicode
Greek, normalized to NFC — the canonical form used throughout this package.

Example:
    >>> from latincy_preprocess.betacode import beta_to_unicode
    >>> beta_to_unicode("a)/eide qea/")
    'ἄειδε θεά'
    >>> beta_to_unicode("*xaldai+kh/n")
    'Χαλδαϊκήν'

.. warning::
    This converter transliterates **every** ASCII letter to Greek. It assumes
    its input is Beta Code, so do not run it on mixed Latin/Greek text — isolate
    the Beta Code spans first. (Latin prose corpora typically mark Greek
    quotations, e.g. between the citation tag and surrounding Latin.)

Attribution
-----------
The substitution and reordering tables (``BETA_REPLACE``, ``BETA_REORDER``) and
the conversion algorithm are adapted from the Classical Language Toolkit (CLTK),
``cltk.alphabet.grc.beta_to_unicode`` (v1 branch), used under the MIT License:

    Copyright (c) 2013 Classical Language Toolkit
    https://github.com/cltk/cltk/blob/v1/src/cltk/alphabet/grc/beta_to_unicode.py

Changes from the original: ported off the third-party ``regex`` dependency to
the standard-library ``re`` module (verified output-equivalent against the CLTK
doctests); patterns are compiled once at import; type hints and an empty-string
fast path added; the original's ``Optional``-as-default-value bug is fixed.
"""

from __future__ import annotations

import re
from unicodedata import normalize

__all__ = [
    "BetaCodeReplacer",
    "beta_to_unicode",
    "is_betacode",
    "BETA_REPLACE",
    "BETA_REORDER",
]

# Heuristic signature of Beta Code: an accent/circumflex following a letter or
# breathing (``i/``, ``a)/``, ``h=``), an iota subscript after a letter (``a|``),
# an asterisk capital marker (``*a``), or a macron/breve escape (``%26``/``%27``).
# Deliberately does NOT treat bare parentheses as a signal, so ordinary Latin
# like "(sic)" is not misread as Beta Code.
_BETA_SIGNAL = re.compile(r"[A-Za-z)(+][/\\=]|[A-Za-z]\||\*[A-Za-z]|%2[67]")


def is_betacode(text: str) -> bool:
    r"""Heuristically report whether ``text`` looks like Beta Code.

    Use this to guard or segment input before :func:`beta_to_unicode`, which
    transliterates *every* ASCII letter and so must not be run on Latin text::

        if is_betacode(span):
            span = beta_to_unicode(span)

    Detection relies on Beta Code's diacritic markers (``/`` ``\\`` ``=`` ``|``,
    ``*`` capitals, ``%26``/``%27``). It is a heuristic, not a proof: Beta Code
    written without any diacritics (e.g. ``"logos"``) is indistinguishable from
    Latin and returns ``False``.

    >>> is_betacode("mh=nin a)/eide")
    True
    >>> is_betacode("Arma virumque cano")
    False
    >>> is_betacode("non accepit ipse (sic)")
    False
    """
    return bool(_BETA_SIGNAL.search(text))

# Ordered (pattern, replacement) pairs. Order matters: uppercase letters (with
# ``*`` markers) resolve first, then lowercase. Once a letter becomes non-ASCII
# Greek, later ASCII patterns no longer match it.
BETA_REPLACE: list[tuple[str, str]] = [
    (r"S|\*[sS]", "Σ"),
    (r"B|\*[bB]", "Β"),
    (r"G|\*[gG]", "Γ"),
    (r"D|\*[dD]", "Δ"),
    (r"Z|\*[zZ]", "Ζ"),
    (r"Q|\*[qQ]", "Θ"),
    (r"K|\*[kK]", "Κ"),
    (r"L|\*[lL]", "Λ"),
    (r"M|\*[mM]", "Μ"),
    (r"N|\*[nN]", "Ν"),
    (r"C|\*[cC]", "Ξ"),
    (r"P|\*[pP]", "Π"),
    (r"R|\*[rR]", "Ρ"),
    (r"T|\*[tT]", "Τ"),
    (r"Y|\*[yY]", "Ψ"),
    (r"X|\*[xX]", "Χ"),
    (r"F|\*[fF]", "Φ"),
    (r"A|\*[aA]", "Α"),
    (r"E|\*[eE]", "Ε"),
    (r"H|\*[hH]", "Η"),
    (r"I|\*[iI]", "Ι"),
    (r"O|\*[oO]", "Ο"),
    (r"U|\*[uU]", "Υ"),
    (r"W|\*[wW]", "Ω"),
    # final sigma: word-final ``s`` (before space/punct or end of string)
    (r"s([ ,.;])", r"ς\1"),
    (r"s\Z", "ς"),
    (r"s", "σ"),
    (r"b", "β"),
    (r"g", "γ"),
    (r"d", "δ"),
    (r"z", "ζ"),
    (r"q", "θ"),
    (r"k", "κ"),
    (r"l", "λ"),
    (r"m", "μ"),
    (r"n", "ν"),
    (r"c", "ξ"),
    (r"p", "π"),
    (r"t", "τ"),
    (r"y", "ψ"),
    (r"x", "χ"),
    (r"f", "φ"),
    (r"r", "ρ"),
    (r"a", "α"),
    (r"e", "ε"),
    (r"h", "η"),
    (r"i", "ι"),
    (r"o", "ο"),
    (r"u", "υ"),
    (r"w", "ω"),
    # lunate sigma
    (r"σ3", "ϲ"),
    (r"Σ3", "Ϲ"),
    (r"σ2", "σ"),
    # koppa
    (r"\*#2", "Ϟ"),
    (r"#2", "ϟ"),
    # koppa (archaic)
    (r"\*#3", "Ϙ"),
    (r"#3", "ϙ"),
    # sampi
    (r"\*#4", "Ϡ"),
    (r"#4", "ϡ"),
    # diacritics — breathings
    (r"\)", "̓"),
    (r"\(", "̔"),
    (r"\+", "̈"),
    # diacritics — accents
    (r"\\", "̀"),
    (r"\/", "́"),
    (r"=", "͂"),
    # subscript iota
    (r"\|", "ͅ"),
    # dot below
    (r"\?", "̣"),
    # breve
    (r"%27", "̆"),
    # macron
    (r"%26", "̄"),
    # punctuation
    (r":", "·"),
    (r"'", "ʼ"),
]

# Reorder diacritic markers into canonical order before substitution: breathing
# / diaeresis first, then accent, then subscript iota.
BETA_REORDER: list[tuple[str, str]] = [
    (r"([\\/=])(\|)?([()+])?", r"\3\1\2"),
    (r"\A(\*)?([()+])?([\\/=])?(\|)?(\w)", r"\1\5\2\3\4"),
]


class BetaCodeReplacer:
    """Convert Beta Code to NFC Unicode Greek.

    Patterns are compiled once per instance. Pass custom ``pattern`` /
    ``reorder_pattern`` lists to override the defaults.

    >>> BetaCodeReplacer().replace_beta_code("OU)=N")
    'οὖν'
    """

    def __init__(
        self,
        pattern: list[tuple[str, str]] | None = None,
        reorder_pattern: list[tuple[str, str]] | None = None,
    ) -> None:
        pattern = BETA_REPLACE if pattern is None else pattern
        reorder_pattern = BETA_REORDER if reorder_pattern is None else reorder_pattern
        self.pattern: list[tuple[re.Pattern[str], str]] = [
            (re.compile(rx), repl) for rx, repl in pattern
        ]
        self.reorder_pattern: list[tuple[re.Pattern[str], str]] = [
            (re.compile(rx), repl) for rx, repl in reorder_pattern
        ]

    def replace_beta_code(self, text: str) -> str:
        """Return ``text`` converted from Beta Code to NFC Unicode Greek."""
        if not text:
            return text
        # If the whole string is uppercase, lowercase everything except the
        # letters explicitly marked uppercase by a leading ``*``.
        if text.isupper():
            text = re.sub(r"(?<!\*)([A-Z]+)", lambda m: m.group(1).lower(), text)
        text = text.replace("-", "")
        for pattern, repl in self.reorder_pattern:
            text = pattern.sub(repl, text)
        for pattern, repl in self.pattern:
            text = pattern.sub(repl, text)
        return normalize("NFC", text)


# Module-level singleton + convenience function (primary API).
_DEFAULT_REPLACER = BetaCodeReplacer()


def beta_to_unicode(text: str) -> str:
    """Convert Beta Code ``text`` to NFC Unicode Greek.

    >>> beta_to_unicode("zei/dwros a)/roura")
    'ζείδωρος ἄρουρα'
    """
    return _DEFAULT_REPLACER.replace_beta_code(text)
