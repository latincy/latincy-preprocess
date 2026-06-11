"""Tests for Beta Code → Unicode conversion (betacode submodule)."""

import unicodedata

import pytest

from latincy_preprocess import beta_to_unicode, is_betacode
from latincy_preprocess.betacode import BetaCodeReplacer

# =============================================================================
# CLTK parity — the upstream doctest cases must still hold after the re port
# =============================================================================


class TestCLTKParity:
    @pytest.mark.parametrize(
        "beta,expected",
        [
            (r"O(/PWS OU)=N MH\ TAU)TO\ ", "ὅπως οὖν μὴ ταὐτὸ "),
            ("PROU+POTETAGME/NWN", "προϋποτεταγμένων"),
            (r"*XALDAI+KH\N", "Χαλδαϊκὴν"),
            ("proi+sxome/nwn", "προϊσχομένων"),
        ],
    )
    def test_upstream_doctests(self, beta, expected):
        assert beta_to_unicode(beta) == expected


# =============================================================================
# Corpus phrases — round-trip consistency with the corpus's Unicode Greek
# =============================================================================


class TestCorpusPhrases:
    def test_homeric_zeidoros_aroura(self):
        # Beta-code form (Apuleius) must match the Unicode form (Pliny).
        assert beta_to_unicode("zei/dwros a)/roura") == "ζείδωρος ἄρουρα"

    @pytest.mark.parametrize(
        "beta,expected",
        [
            ("fe/rei", "φέρει"),
            ("polla\\", "πολλὰ"),
            ("me\\n", "μὲν"),
            ("th=|", "τῇ"),
            ("h(patiko\\n", "ἡπατικὸν"),
            ("a)/eide", "ἄειδε"),
        ],
    )
    def test_phrases(self, beta, expected):
        assert beta_to_unicode(beta) == expected


# =============================================================================
# Letters, sigma, capitals
# =============================================================================


class TestLetters:
    def test_lowercase_alphabet(self):
        assert beta_to_unicode("abgdezhqiklmncoprstufxyw") == (
            "αβγδεζηθικλμνξοπρστυφχψω"
        )

    def test_medial_vs_final_sigma(self):
        assert beta_to_unicode("sofos") == "σοφος"  # medial σ, final ς
        assert beta_to_unicode("sos sos") == "σος σος"  # final ς before space and at end

    def test_final_sigma_end_of_string(self):
        assert beta_to_unicode("lo/gos") == "λόγος"

    def test_final_sigma_before_punctuation(self):
        assert beta_to_unicode("lo/gos,") == "λόγος,"

    def test_capital_via_asterisk(self):
        assert beta_to_unicode("*a") == "Α"
        assert beta_to_unicode("*s") == "Σ"

    def test_all_uppercase_input(self):
        assert beta_to_unicode("LO/GOS") == "λόγος"


# =============================================================================
# Diacritics
# =============================================================================


class TestDiacritics:
    def test_smooth_breathing(self):
        assert beta_to_unicode("a)") == "ἀ"

    def test_rough_breathing(self):
        assert beta_to_unicode("a(") == "ἁ"

    def test_acute_grave_circumflex(self):
        assert beta_to_unicode("a/") == "ά"
        assert beta_to_unicode("a\\") == "ὰ"
        assert beta_to_unicode("a=") == "ᾶ"

    def test_iota_subscript(self):
        assert beta_to_unicode("a|") == "ᾳ"

    def test_diaeresis(self):
        assert beta_to_unicode("i+") == "ϊ"

    def test_breathing_and_accent_combined(self):
        assert beta_to_unicode("a)/") == "ἄ"


# =============================================================================
# Output form and edge cases
# =============================================================================


class TestOutputAndEdges:
    def test_output_is_nfc(self):
        out = beta_to_unicode("a)/nqrwpos")
        assert unicodedata.normalize("NFC", out) == out

    def test_empty_string(self):
        assert beta_to_unicode("") == ""

    def test_whitespace_only(self):
        assert beta_to_unicode("   ") == "   "

    def test_class_matches_function(self):
        replacer = BetaCodeReplacer()
        text = "mh=nin a)/eide qea\\"
        assert replacer.replace_beta_code(text) == beta_to_unicode(text)

    def test_custom_pattern_override(self):
        # A trivial custom table should be honored (no default fallthrough).
        replacer = BetaCodeReplacer(pattern=[(r"a", "X")], reorder_pattern=[])
        assert replacer.replace_beta_code("aaa") == "XXX"


# =============================================================================
# is_betacode — heuristic guardrail
# =============================================================================


class TestIsBetacode:
    @pytest.mark.parametrize(
        "beta",
        [
            "mh=nin a)/eide",
            "zei/dwros a)/roura",
            "polla\\",
            "th=|",
            "*XALDAI+KH\\N",
            "a)/eide",  # breathing+accent stacked on initial vowel
        ],
    )
    def test_detects_betacode(self, beta):
        assert is_betacode(beta) is True

    @pytest.mark.parametrize(
        "latin",
        [
            "Arma virumque cano",
            "non accepit ipse (sic)",  # parentheses must not trigger
            "Gallia est omnis divisa in partes tres",
            "",
            "logos",  # diacritic-free beta-code is indistinguishable -> False
        ],
    )
    def test_rejects_non_betacode(self, latin):
        assert is_betacode(latin) is False

    def test_guards_conversion(self):
        # The documented usage pattern: only convert spans that look like beta.
        span = "a)/nqrwpos"
        result = beta_to_unicode(span) if is_betacode(span) else span
        assert result == "ἄνθρωπος"
        latin = "homo"
        result = beta_to_unicode(latin) if is_betacode(latin) else latin
        assert result == "homo"  # left untouched
