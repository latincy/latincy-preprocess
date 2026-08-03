"""
Tests for the Ancient Greek normalization module (latincy_preprocess.grc).

Covers the canonical elision standard (all apostrophe encodings -> U+2019),
macron/breve stripping, lookup-key folding, and is_greek_word — plus a parity
check against latincy-grc-pipelines' pre-consolidation behavior for the exact
cases that motivated this module (Tesserae-style elision: μυρίʼ, ἀπερείσιʼ).
"""

import pytest

from latincy_preprocess.grc import (
    is_greek_word,
    normalize_lookup_key,
    normalize_norm,
    normalize_surface,
)


# =============================================================================
# normalize_surface
# =============================================================================


class TestNormalizeSurface:
    def test_ascii_apostrophe_to_u2019(self):
        assert normalize_surface("ἀλλ'") == "ἀλλ’"

    def test_modifier_letter_apostrophe_to_u2019(self):
        # Tesserae's convention (U+02BC)
        assert normalize_surface("μυρίʼ") == "μυρί’"

    def test_psili_pneumon_to_u2019(self):
        assert normalize_surface("ἀλλ᾿") == "ἀλλ’"

    def test_dangling_combining_elision_to_u2019(self):
        # Perseus Betacode-conversion artifact: combining smooth breathing
        # misused as an elision mark on a consonant.
        assert normalize_surface("ἀλλ̓") == "ἀλλ’"

    def test_already_canonical_is_idempotent(self):
        assert normalize_surface("δ’") == "δ’"

    def test_macron_stripped(self):
        assert normalize_surface("φῡσις") == "φυσις"

    def test_breve_stripped(self):
        assert normalize_surface("δῐκαστής") == "δικαστής"

    def test_smooth_breathing_not_mistaken_for_elision(self):
        # Legitimate breathing composes onto the vowel under NFC; must not
        # become an elision mark.
        assert normalize_surface("ἀγαθός") == "ἀγαθός"

    def test_breathing_blocked_only_by_length_mark_not_mistaken_for_elision(self):
        # Regression: Wiktionary marks vowel length AND breathing together
        # (breve + breathing), which has no single precomposed Unicode
        # codepoint — NFC alone leaves the breathing dangling purely because
        # the breve is in the way, not because it's elision. Observed:
        # ᾰ̓γγέλλω (alpha+breve, U+313) was corrupted to α’γγέλλω instead of
        # ἀγγέλλω before macron/breve stripping was moved ahead of the
        # dangling-U+0313 check.
        assert normalize_surface("ᾰ̓γγέλλω") == "ἀγγέλλω"

    def test_empty_string(self):
        assert normalize_surface("") == ""


# =============================================================================
# normalize_norm
# =============================================================================


class TestNormalizeNorm:
    def test_closed_class_elision_restored(self):
        assert normalize_norm("δ’") == "δέ"
        assert normalize_norm("τ’") == "τε"
        assert normalize_norm("ἀλλ’") == "ἀλλά"

    def test_any_apostrophe_variant_restores(self):
        # normalize_norm must surface-normalize first, or ELISION can't fire.
        assert normalize_norm("δ'") == "δέ"
        assert normalize_norm("δʼ") == "δέ"

    def test_content_word_elision_not_restored(self):
        # greek-normalisation only restores a closed set of functors; general
        # content-word elision (epic/poetic) is a known, separate gap — this
        # module must not silently guess.
        assert normalize_norm("μυρί’") == "μυρί’"


# =============================================================================
# normalize_lookup_key
# =============================================================================


class TestNormalizeLookupKey:
    def test_grave_folds_to_acute(self):
        assert normalize_lookup_key("φονὸς") == "φονός"

    def test_final_sigma_folded(self):
        assert normalize_lookup_key("λογοσ") == "λογος"

    def test_macron_stripped(self):
        assert normalize_lookup_key("φῡσις") == "φυσις"

    def test_elision_apostrophe_canonicalized_even_without_prior_normalize_surface(self):
        # A caller that hands raw, un-normalized extraction text straight to
        # normalize_lookup_key (e.g. a corpus extractor) must still get a
        # single canonical elision codepoint out.
        assert "’" in normalize_lookup_key("μυρίʼ")
        assert normalize_lookup_key("μυρί'") == normalize_lookup_key("μυρίʼ")


# =============================================================================
# is_greek_word
# =============================================================================


class TestIsGreekWord:
    def test_plain_greek_word(self):
        assert is_greek_word("ἄνθρωπος")

    def test_elided_word_is_valid(self):
        assert is_greek_word("δ’")
        assert is_greek_word("μυρί’")

    def test_rejects_latin(self):
        assert not is_greek_word("anthropos")

    def test_rejects_non_canonical_apostrophe(self):
        # Only the canonical U+2019 is accepted here; callers are expected to
        # run normalize_surface first (see extractor call sites).
        assert not is_greek_word("δ'")

    def test_rejects_empty(self):
        assert not is_greek_word("")

    def test_rejects_overlong(self):
        assert not is_greek_word("α" * 51)


# =============================================================================
# Parity: the exact cases that motivated this consolidation
# (Tesserae elision report: 465/5139 tokens in one book had lemma == elided
# surface, apostrophe included, because these forms never reached the lemma
# lookup table — see latincy-grc-words extraction fixes.)
# =============================================================================


@pytest.mark.parametrize(
    "raw,expected_surface",
    [
        ("μυρίʼ", "μυρί’"),
        ("δʼ", "δ’"),
        ("τʼ", "τ’"),
        ("ἀπερείσιʼ", "ἀπερείσι’"),
    ],
)
def test_tesserae_elision_forms_canonicalize(raw, expected_surface):
    assert normalize_surface(raw) == expected_surface
