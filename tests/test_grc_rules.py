"""
Tests for the Ancient Greek normalization module (latincy_preprocess.grc).

Covers the canonical elision standard (all apostrophe encodings -> U+2019),
macron/breve stripping, lookup-key folding, and is_greek_word — plus a parity
check against latincy-grc-pipelines' pre-consolidation behavior for the exact
cases that motivated this module (Tesserae-style elision: μυρίʼ, ἀπερείσιʼ).
"""

import pytest

from latincy_preprocess.grc import (
    GRC_ELISION_EXTRA,
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

    def test_keraia_is_not_an_elision_mark(self):
        # Greek numeral sign (keraia): U+0374 has a canonical decomposition to
        # U+02B9 MODIFIER LETTER PRIME, so plain NFC silently folds δʹ(U+0374)
        # -> δʹ(U+02B9). Neither codepoint may be treated as an elision
        # apostrophe: δʹ is the numeral 4, and collapsing it to δ’ would make
        # it byte-identical to elided δέ — the gold corpus keeps 1,800+ NUM
        # tokens on the U+02B9 form. This pins the (intentional) asymmetry.
        keraia_0374 = "δ" + chr(0x0374)  # explicit codepoints: the two
        keraia_02b9 = "δ" + chr(0x02B9)  # keraia forms look identical
        assert normalize_surface(keraia_0374) == keraia_02b9  # NFC fold only
        assert normalize_surface(keraia_02b9) == keraia_02b9  # untouched
        assert "’" not in normalize_surface(keraia_0374)
        assert normalize_norm(keraia_02b9) == keraia_02b9     # no restoration


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

    def test_epic_elision_restored_via_latincy_overlay(self):
        # The library's ELISION map is NT-oriented; the LatinCy overlay
        # (GRC_ELISION_EXTRA) covers the epic/tragic set that previously
        # leaked the elided surface as norm AND lemma (external Homer report:
        # ἄρ’ 581×, κ’ 239×, θ’ 219×, ...).
        assert normalize_norm("ἄρ’") == "ἄρα"
        assert normalize_norm("ἄρʼ") == "ἄρα"  # U+02BC input, as Perseus ships
        assert normalize_norm("κ’") == "κε"
        assert normalize_norm("θ’") == "τε"     # de-aspirated
        assert normalize_norm("ἔνθ’") == "ἔνθα"
        assert normalize_norm("μάλ’") == "μάλα"
        assert normalize_norm("οὔτ’") == "οὔτε"
        assert normalize_norm("ἔπειτ’") == "ἔπειτα"
        assert normalize_norm("μέγ’") == "μέγα"   # form in isolation, not lemma
        assert normalize_norm("πόλλ’") == "πολλά"  # accent restored with the vowel
        assert normalize_norm("ῥ’") == "ῥα"

    def test_capitalized_elision_restores_via_titlecase_fallback(self):
        assert normalize_norm("Ἔνθ’") == "Ἔνθα"
        assert normalize_norm("Ἄλλ’") == "Ἄλλα"

    def test_capitalized_elision_covers_the_library_map_too(self):
        # The titlecase fallback must re-run the lowercased form through the
        # LIBRARY map as well as the overlay. Consulting the overlay alone
        # restored only its own 54 entries and left all 36 library entries
        # capital-broken — including sentence-initial Ἀλλ’/Οὐδ’/Δ’, which are
        # exactly the case the fallback exists for.
        assert normalize_norm("Ἀλλ’") == "Ἀλλά"
        assert normalize_norm("Οὐδ’") == "Οὐδέ"
        assert normalize_norm("Κατ’") == "Κατά"
        assert normalize_norm("Καθ’") == "Κατά"  # aspirated
        assert normalize_norm("Δ’") == "Δέ"
        assert normalize_norm("Μ’") == "Με"
        assert normalize_norm("Μήδ’") == "Μηδέ"  # accent shifts with restoration
        assert normalize_norm("Σ’") == "Σε"      # ς’/σ’ final-sigma encoding

    def test_every_elision_entry_restores_in_both_cases(self):
        # Exhaustive: no entry in either map may leak an elided surface, in
        # either casing. Guards against a future entry being added in a form
        # whose capital does not round-trip.
        from greek_normalisation.norm_data import ELISION

        for mapping in (ELISION, GRC_ELISION_EXTRA):
            for elided, restored in mapping.items():
                assert normalize_norm(elided) == restored
                cap = elided[:1].upper() + elided[1:]
                if cap != elided:
                    assert normalize_norm(cap) == restored[:1].upper() + restored[1:]

    def test_capitalized_ambiguous_elision_still_not_restored(self):
        # The fallback must not become a back door around the curation policy.
        assert normalize_norm("Μυρί’") == "Μυρί’"
        assert normalize_norm("Αὖθ’") == "Αὖθ’"
        assert normalize_norm("Ἔστ’") == "Ἔστ’"

    def test_ambiguous_elision_not_restored(self):
        # Restorations the overlay must NOT guess: content words with
        # uncertain vocalism (μυρί’) and genuinely ambiguous functors
        # (αὖθ’ = αὖτε or αὖθι; ἔστ’ = ἐστί or ἔστε). These stay elided.
        assert normalize_norm("μυρί’") == "μυρί’"
        assert normalize_norm("αὖθ’") == "αὖθ’"
        assert normalize_norm("ἔστ’") == "ἔστ’"

    def test_overlay_does_not_shadow_library_map(self):
        # Library entries keep their library values (overlay fires only when
        # the library map misses).
        assert normalize_norm("ταῦθ’") == "ταῦτα"
        assert normalize_norm("ποτ’") == "ποτε"


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
