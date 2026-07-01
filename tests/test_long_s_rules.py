"""
Tests for Long-S normalization.

Generated from manually validated data:
- 54 approved corrections (100% accuracy)
- 107 allowlisted words (legitimate f- words that must be preserved)
"""

import json
from pathlib import Path

import pytest

from latincy_preprocess.long_s import LongSNormalizer

DATA_DIR = Path(__file__).parent / "data"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def normalizer():
    """Fresh LongSNormalizer instance for each test."""
    return LongSNormalizer()


@pytest.fixture
def approved_corrections():
    """Load the 54 manually approved corrections."""
    path = DATA_DIR / "approved_corrections.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def allowlist():
    """Load the allowlist of legitimate f- words."""
    path = DATA_DIR / "allowlist.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ===========================================================================
# Section 1: Approved corrections -- the normalizer must reproduce all 54
# ===========================================================================

def _load_approved_corrections():
    path = DATA_DIR / "approved_corrections.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    pairs = []
    for key in data:
        ocr_form, expected = key.split("\u2192")
        pairs.append((ocr_form, expected))
    return pairs


@pytest.mark.parametrize(
    "ocr_form,expected",
    _load_approved_corrections(),
    ids=[f"{ocr}->{exp}" for ocr, exp in _load_approved_corrections()],
)
def test_approved_correction(normalizer, ocr_form, expected):
    result, _rules = normalizer.normalize_word_full(ocr_form, apply_pass2=True)
    assert result == expected, (
        f"Approved correction failed: {ocr_form!r} -> expected {expected!r}, got {result!r}"
    )


# ===========================================================================
# Section 2: Allowlist preservation
# ===========================================================================

def _load_allowlist():
    path = DATA_DIR / "allowlist.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("word", _load_allowlist())
def test_allowlist_preserved(normalizer, word):
    result, _rules = normalizer.normalize_word_full(word, apply_pass2=True)
    assert result == word, (
        f"Allowlisted word was incorrectly modified: {word!r} -> {result!r}"
    )


# ===========================================================================
# Section 3: Pass 1 high-confidence rules
# ===========================================================================

class TestPass1Rules:
    def test_ft_to_st(self, normalizer):
        result, rules = normalizer.normalize_word_pass1("ftatua")
        assert result == "statua"
        assert any("ft" in r for r in rules)

    def test_fp_to_sp(self, normalizer):
        result, rules = normalizer.normalize_word_pass1("fpiritus")
        assert result == "spiritus"
        assert any("fp" in r for r in rules)

    def test_fc_to_sc(self, normalizer):
        result, rules = normalizer.normalize_word_pass1("fcilicet")
        assert result == "scilicet"
        assert any("fc" in r for r in rules)

    def test_fqu_to_squ(self, normalizer):
        result, rules = normalizer.normalize_word_pass1("fquam")
        assert result == "squam"
        assert any("fqu" in r for r in rules)

    def test_fpe_to_spe(self, normalizer):
        result, rules = normalizer.normalize_word_pass1("fpecies")
        assert result == "species"
        assert any("fpe" in r for r in rules)

    def test_fuf_to_sus(self, normalizer):
        result, rules = normalizer.normalize_word_pass1("fufpiciens")
        assert result == "suspiciens"

    def test_fum_to_sum(self, normalizer):
        result, rules = normalizer.normalize_word_pass1("fumma")
        assert result == "summa"
        assert any("fum" in r for r in rules)

    def test_multiple_rules_apply(self, normalizer):
        result, rules = normalizer.normalize_word_pass1("tranfponere")
        assert result == "transponere"

    def test_medial_fp(self, normalizer):
        result, rules = normalizer.normalize_word_pass1("profpera")
        assert result == "prospera"

    def test_no_false_positive_on_clean_word(self, normalizer):
        result, rules = normalizer.normalize_word_pass1("dominus")
        assert result == "dominus"
        assert rules == []

    def test_poff_to_poss(self, normalizer):
        """poff is an impossible Latin 4-gram (zero corpus presence);
        poff→poss is a high-confidence Pass 1 rule like ft/fp/fc."""
        result, rules = normalizer.normalize_word_pass1("poffe")
        assert result == "posse"
        assert any("poff" in r for r in rules)

    def test_poff_family(self, normalizer):
        """poff→poss applies across the posse/possum/possideo family."""
        cases = {"poffum": "possum", "poffideo": "possideo", "poffibile": "possibile"}
        for ocr, expected in cases.items():
            result, _ = normalizer.normalize_word_pass1(ocr)
            assert result == expected, f"{ocr} → expected {expected}, got {result}"


# ===========================================================================
# Section 4: Word-final f -> s
# ===========================================================================

class TestWordFinalF:
    def test_word_final_f_simple(self, normalizer):
        result, rules = normalizer.normalize_word_pass1("ef")
        assert result == "es"
        assert any("word-final" in r for r in rules)

    def test_word_final_f_longer_word(self, normalizer):
        result, rules = normalizer.normalize_word_pass1("poteft")
        assert result == "potest"

    def test_word_final_f_with_prefix(self, normalizer):
        result, rules = normalizer.normalize_word_pass1("fenatuf")
        assert result == "fenatus"

    def test_single_f(self, normalizer):
        result, rules = normalizer.normalize_word_pass1("f")
        assert result == "s"

    def test_word_ending_in_non_f(self, normalizer):
        result, rules = normalizer.normalize_word_pass1("rex")
        assert result == "rex"
        assert not any("word-final" in r for r in rules)


# ===========================================================================
# Section 5: Pass 2 context-dependent rules
# ===========================================================================

class TestPass2Rules:
    def test_fu_to_su_common(self, normalizer):
        result, rules = normalizer.normalize_word_full("funt", apply_pass2=True)
        assert result == "sunt", f"Expected 'sunt', got {result!r}"

    def test_fe_to_se_common(self, normalizer):
        result, rules = normalizer.normalize_word_full("fed", apply_pass2=True)
        assert result == "sed", f"Expected 'sed', got {result!r}"

    def test_allowlist_blocks_pass2(self, normalizer):
        result, rules = normalizer.normalize_word_full("fuit", apply_pass2=True)
        assert result == "fuit"

    def test_allowlist_fe_blocks_pass2(self, normalizer):
        result, rules = normalizer.normalize_word_full("fecit", apply_pass2=True)
        assert result == "fecit"

    def test_pass2_disabled(self, normalizer):
        result, rules = normalizer.normalize_word_full("funt", apply_pass2=False)
        assert result == "funt"


# ===========================================================================
# Section 6: Text-level normalization
# ===========================================================================

class TestTextNormalization:
    def test_text_pass1(self, normalizer):
        text = "ftatua fpiritus fcilicet"
        result = normalizer.normalize_text_pass1(text)
        assert result == "statua spiritus scilicet"

    def test_text_full(self, normalizer):
        text = "funt ftatua fundamentum"
        result = normalizer.normalize_text_full(text, apply_pass2=True)
        assert result == "sunt statua fundamentum"

    def test_empty_text(self, normalizer):
        result = normalizer.normalize_text_full("")
        assert result == ""

    def test_single_word_text(self, normalizer):
        result = normalizer.normalize_text_full("fpiritus")
        assert result == "spiritus"

    def test_preserves_spacing(self, normalizer):
        result = normalizer.normalize_text_full("rex   dominus")
        assert result == "rex dominus"

    def test_text_case_preservation(self, normalizer):
        result = normalizer.normalize_text_full("Sic uita eft", apply_pass2=True)
        assert result == "Sic uita est"

    def test_text_allcaps_preservation(self, normalizer):
        result = normalizer.normalize_text_full("FTATUA FPIRITUS", apply_pass2=True)
        assert result == "STATUA SPIRITUS"


# ===========================================================================
# Section 7: Edge cases and robustness
# ===========================================================================

class TestEdgeCases:
    def test_empty_word_pass1(self, normalizer):
        result, rules = normalizer.normalize_word_pass1("")
        assert result == ""
        assert rules == []

    def test_empty_word_full(self, normalizer):
        result, rules = normalizer.normalize_word_full("")
        assert result == ""

    def test_single_character_non_f(self, normalizer):
        result, rules = normalizer.normalize_word_pass1("a")
        assert result == "a"

    def test_all_f_word(self, normalizer):
        result, rules = normalizer.normalize_word_pass1("fff")
        assert result == "ffs"

    def test_uppercase_preserved(self, normalizer):
        result, rules = normalizer.normalize_word_pass1("FTATUA")
        assert result == "STATUA"

    def test_mixed_case_title(self, normalizer):
        result, rules = normalizer.normalize_word_pass1("Fpiritus")
        assert result == "Spiritus"

    def test_lowercase_unchanged(self, normalizer):
        result, rules = normalizer.normalize_word_pass1("ftatua")
        assert result == "statua"

    def test_numeric_input(self, normalizer):
        result, rules = normalizer.normalize_word_pass1("123")
        assert result == "123"
        assert rules == []

    def test_punctuation_attached(self, normalizer):
        result, rules = normalizer.normalize_word_pass1("eft,")
        assert "st" in result

    def test_non_latin_characters(self, normalizer):
        result, rules = normalizer.normalize_word_pass1("\u03b1\u03b2\u03b3")
        assert result == "\u03b1\u03b2\u03b3"
        assert rules == []

    def test_actual_long_s_character(self, normalizer):
        result, rules = normalizer.normalize_word_pass1("\u017ftatua")
        assert result == "\u017ftatua"


# ===========================================================================
# Section 8: Statistics tracking
# ===========================================================================

class TestStatistics:
    def test_stats_count_words(self, normalizer):
        normalizer.normalize_text_pass1("eft fpiritus rex")
        assert normalizer.stats["total_words"] == 3

    def test_stats_count_modified(self, normalizer):
        normalizer.normalize_text_pass1("eft fpiritus rex")
        assert normalizer.stats["words_modified"] == 2

    def test_stats_reset(self, normalizer):
        normalizer.normalize_text_pass1("eft fpiritus")
        normalizer.reset_statistics()
        assert normalizer.stats["total_words"] == 0
        assert normalizer.stats["words_modified"] == 0
        assert normalizer.stats["transformations"] == {}

    def test_stats_track_transformations(self, normalizer):
        normalizer.normalize_word_pass1("ftatua")
        assert "ft \u2192 st" in normalizer.stats["transformations"]


# ===========================================================================
# Section 9: Regression tests from known corpus examples
# ===========================================================================

class TestCorpusRegressions:
    def test_christus_family(self, normalizer):
        cases = {
            "chriftus": "christus",
            "chriftum": "christum",
            "chrifti": "christi",
            "chrifto": "christo",
            "chriftiani": "christiani",
        }
        for ocr, expected in cases.items():
            result, _ = normalizer.normalize_word_pass1(ocr)
            assert result == expected, f"{ocr} -> expected {expected}, got {result}"

    def test_noster_family(self, normalizer):
        cases = {
            "noftra": "nostra",
            "noftram": "nostram",
            "noftro": "nostro",
            "noftre": "nostre",
            "noftris": "nostris",
            "noftri": "nostri",
            "noftrum": "nostrum",
        }
        for ocr, expected in cases.items():
            result, _ = normalizer.normalize_word_pass1(ocr)
            assert result == expected, f"{ocr} -> expected {expected}, got {result}"

    def test_ipsum_family(self, normalizer):
        result, _ = normalizer.normalize_word_pass1("ipfum")
        assert result == "ipsum"

    def test_spiritus_family(self, normalizer):
        cases = {
            "fpiritus": "spiritus",
            "fpiritualis": "spiritualis",
            "fpiritu": "spiritu",
        }
        for ocr, expected in cases.items():
            result, _ = normalizer.normalize_word_pass1(ocr)
            assert result == expected, f"{ocr} -> expected {expected}, got {result}"

    def test_compound_corrections(self, normalizer):
        result, _ = normalizer.normalize_word_full("feipfum", apply_pass2=True)
        assert result == "seipsum"

        result, _ = normalizer.normalize_word_full("teipfum", apply_pass2=True)
        assert result == "teipsum"


# ===========================================================================
# Section 10: Word-initial fo → so
# ===========================================================================

class TestWordInitialFo:
    """Pass 2 should handle word-initial fo → so using n-gram frequencies."""

    def test_folitudinem(self, normalizer):
        result, _ = normalizer.normalize_word_full("folitudinem", apply_pass2=True)
        assert result == "solitudinem"

    def test_folus(self, normalizer):
        result, _ = normalizer.normalize_word_full("folus", apply_pass2=True)
        assert result == "solus"

    def test_folet(self, normalizer):
        result, _ = normalizer.normalize_word_full("folet", apply_pass2=True)
        assert result == "solet"

    def test_forum_preserved(self, normalizer):
        """forum is a legitimate Latin word — must NOT be changed."""
        result, _ = normalizer.normalize_word_full("forum", apply_pass2=True)
        assert result == "forum"

    def test_forma_preserved(self, normalizer):
        """forma is legitimate — must NOT be changed."""
        result, _ = normalizer.normalize_word_full("forma", apply_pass2=True)
        assert result == "forma"

    def test_fortis_preserved(self, normalizer):
        """fortis is legitimate — must NOT be changed."""
        result, _ = normalizer.normalize_word_full("fortis", apply_pass2=True)
        assert result == "fortis"


# ===========================================================================
# Section 11: Medial long-s detection
# ===========================================================================

class TestMedialLongS:
    """Medial f (not word-initial) should be corrected when n-gram
    evidence strongly favours s in that position."""

    def test_obfecro(self, normalizer):
        result, _ = normalizer.normalize_word_full("obfecro", apply_pass2=True)
        assert result == "obsecro"

    def test_abfens(self, normalizer):
        result, _ = normalizer.normalize_word_full("abfens", apply_pass2=True)
        assert result == "absens"

    def test_obftetricemaccerfo(self, normalizer):
        """Multiple medial long-s in a merged word."""
        result, _ = normalizer.normalize_word_full("obftetricemaccerfo", apply_pass2=True)
        assert result == "obstetricemaccerso"

    def test_deferas_preserved(self, normalizer):
        """deferas has legitimate medial f (de + fero)."""
        result, _ = normalizer.normalize_word_full("deferas", apply_pass2=True)
        assert result == "deferas"

    def test_confilio_preserved(self, normalizer):
        """confilio has legitimate medial f (con + filio)."""
        result, _ = normalizer.normalize_word_full("confilio", apply_pass2=True)
        assert result == "confilio"

    def test_proficifcor(self, normalizer):
        """proficifcor → proficiscor: medial ft caught by pass1, but
        the first f (pro+ficiscor) is legitimate."""
        result, _ = normalizer.normalize_word_full("proficifcor", apply_pass2=True)
        assert result == "proficiscor"


# ===========================================================================
# Section 12: Regression — false positives (correct Latin wrongly altered)
# Surfaced in latincy-pretrain D3 corpus-correction QA, 2026-06-30.
# ===========================================================================

class TestFalsePositiveRegressions:
    """Words Pass 2 must NOT alter — they are genuine Latin, not OCR long-s."""

    # --- medial f protection (via _F_STEMS 'fel' entry) ---

    def test_infelix_preserved(self, normalizer):
        """infelix: medial 'f' is from the felix root (in+felix);
        must not become 'inselix' via the medial nf→ns trigram rule."""
        result, _ = normalizer.normalize_word_full("infelix", apply_pass2=True)
        assert result == "infelix"

    def test_infelicis_preserved(self, normalizer):
        """infelicis: genitive of infelix; medial f from felix root."""
        result, _ = normalizer.normalize_word_full("infelicis", apply_pass2=True)
        assert result == "infelicis"

    # --- word-initial f protection: stem-aware ('fel' prefix) ---
    # These words are NOT in the word-exact allowlist; they must be protected
    # by the 'fel' stem prefix check, not by individual enumeration.

    def test_felicitas_preserved(self, normalizer):
        """felicitas: stem-aware 'fel' prefix should protect this and all inflections."""
        result, _ = normalizer.normalize_word_full("felicitas", apply_pass2=True)
        assert result == "felicitas"

    def test_felicitas_inflected_forms_preserved(self, normalizer):
        """All standard inflections of felicitas — covered by 'fel' stem, not word list."""
        for word in ["felicitatis", "felicitatem", "felicitati", "felicitate"]:
            result, _ = normalizer.normalize_word_full(word, apply_pass2=True)
            assert result == word, f"Expected {word!r} preserved, got {result!r}"

    def test_felicissimus_preserved(self, normalizer):
        """felicissimus (superlative): not in the word list — stem check only."""
        result, _ = normalizer.normalize_word_full("felicissimus", apply_pass2=True)
        assert result == "felicissimus"

    def test_feliciori_preserved(self, normalizer):
        """feliciori (comparative dative): not in the word list — stem check only."""
        result, _ = normalizer.normalize_word_full("feliciori", apply_pass2=True)
        assert result == "feliciori"

    # --- word-initial f protection: stem-aware ('fest' prefix) ---

    def test_festus_preserved(self, normalizer):
        """festus: nominative singular — covered by 'fest' stem, not word list."""
        result, _ = normalizer.normalize_word_full("festus", apply_pass2=True)
        assert result == "festus"

    def test_festivus_preserved(self, normalizer):
        """festivus: not in the word list — stem 'fest' check only."""
        result, _ = normalizer.normalize_word_full("festivus", apply_pass2=True)
        assert result == "festivus"

    def test_festivitate_preserved(self, normalizer):
        """festivitate: not in the word list — stem 'fest' check only."""
        result, _ = normalizer.normalize_word_full("festivitate", apply_pass2=True)
        assert result == "festivitate"

    # --- word-exact one-off ---

    def test_fere_preserved(self, normalizer):
        """fere: common adverb with no morphological family; stays word-exact."""
        result, _ = normalizer.normalize_word_full("fere", apply_pass2=True)
        assert result == "fere"

    # --- fero passive / missing active forms ---
    # The allowlist had all active forms of fero but was missing the passive
    # paradigm and a handful of active forms.  Without these entries, Pass 2
    # flips word-initial fe→se via the <fe vs <se trigram heuristic.

    @pytest.mark.parametrize("word", [
        # present passive
        "feror", "ferris", "ferimur", "ferimini",
        # imperfect active (missing slots)
        "ferebas", "ferebamus", "ferebatis",
        # future active (missing)
        "feretis",
        # imperfect passive
        "ferebar", "ferebaris", "ferebamur", "ferebamini", "ferebantur",
        # future passive
        "ferar", "fereris", "feretur", "feremur", "feremini", "ferentur",
        # gerundive
        "ferendus", "ferenda",
    ])
    def test_fero_passive_and_missing_forms_preserved(self, normalizer, word):
        """Missing fero forms must not be converted by the fe→se heuristic."""
        result, _ = normalizer.normalize_word_full(word, apply_pass2=True)
        assert result == word, f"Expected {word!r} preserved, got {result!r}"


# ===========================================================================
# Section 13: Regression — false negatives (real long-s OCR errors missed)
# ===========================================================================

class TestFalseNegativeRegressions:
    """OCR long-s artifacts that Pass 2 must correct but previously missed."""

    def test_accenfus_corrected(self, normalizer):
        """accenfus → accensus: medial 'nf' is an OCR long-s artifact.
        Previously blocked by the over-broad 'fus' entry in _F_STEMS,
        which was intended for the fundo family (confusus, diffusus, …)
        but also matched the word-final '-fus' in 'accenfus'."""
        result, _ = normalizer.normalize_word_full("accenfus", apply_pass2=True)
        assert result == "accensus"


# ===========================================================================
# Section 14: Double-f (ff → ss) OCR correction
# Medial '-ff-' clusters are an early-modern long-s artifact: the compositor
# set two long-s glyphs for '-ss-', OCR reads them both as 'f'.
# 4-gram evidence drives the correction; _F_STEMS guards genuine Latin
# compounds (ex/ob/ad + f-root) from false conversion.
# Known miss: poffe→posse cannot be corrected safely — offe:374 vs osse:521
# is only 1.4× at the 4-gram level, below the 2.0 threshold.
# ===========================================================================

class TestDoubleF:
    """Pass 2 must correct medial ff→ss when n-gram evidence is clear."""

    # --- OCR corrections (false negatives fixed by double-f pass) ---

    def test_gloffario_corrected(self, normalizer):
        """Gloffario → Glossario: 4-gram offa:1 vs ossa:59 (59×)."""
        result, _ = normalizer.normalize_word_full("Gloffario", apply_pass2=True)
        assert result == "Glossario"

    def test_claffis_corrected(self, normalizer):
        """claffis → classis: 4-gram affi:51 vs assi:584 (11.5×)."""
        result, _ = normalizer.normalize_word_full("claffis", apply_pass2=True)
        assert result == "classis"

    def test_miffus_corrected(self, normalizer):
        """miffus → missus: 4-gram iffu:26 vs issu:216 (8.3×)."""
        result, _ = normalizer.normalize_word_full("miffus", apply_pass2=True)
        assert result == "missus"

    def test_paffus_corrected(self, normalizer):
        """paffus → passus: 4-gram affu:5 vs assu:350 (70×)."""
        result, _ = normalizer.normalize_word_full("paffus", apply_pass2=True)
        assert result == "passus"

    def test_neceffe_corrected(self, normalizer):
        """neceffe → necesse: 4-gram effe:754 vs esse:6717 (8.9×)."""
        result, _ = normalizer.normalize_word_full("neceffe", apply_pass2=True)
        assert result == "necesse"

    def test_poffe_corrected(self, normalizer):
        """poffe → posse: poff has zero corpus presence so it is a Pass 1 rule,
        not a 4-gram heuristic (offe:374/osse:521 is only 1.4×, below threshold)."""
        result, _ = normalizer.normalize_word_full("poffe", apply_pass2=True)
        assert result == "posse"

    # --- Legitimate Latin ff-compounds must NOT be altered ---
    # Without _F_STEMS protection on the second-f tail, all of these would
    # fire: effectus (8.9×), officium (8.7×), efficio (3.4×), afferens (2.9×).

    def test_effectus_preserved(self, normalizer):
        """effectus: second-f tail 'fectus' starts with 'fect' → _F_STEMS blocks."""
        result, _ = normalizer.normalize_word_full("effectus", apply_pass2=True)
        assert result == "effectus"

    def test_officium_preserved(self, normalizer):
        """officium: second-f tail 'ficium' starts with 'fic' → _F_STEMS blocks."""
        result, _ = normalizer.normalize_word_full("officium", apply_pass2=True)
        assert result == "officium"

    def test_efficio_preserved(self, normalizer):
        """efficio: second-f tail 'ficio' starts with 'fic' → _F_STEMS blocks."""
        result, _ = normalizer.normalize_word_full("efficio", apply_pass2=True)
        assert result == "efficio"

    def test_afferens_preserved(self, normalizer):
        """afferens: second-f tail 'ferens' starts with 'fer' → _F_STEMS blocks."""
        result, _ = normalizer.normalize_word_full("afferens", apply_pass2=True)
        assert result == "afferens"

    def test_effulget_preserved(self, normalizer):
        """effulget: second-f tail 'fulget' — needs 'ful' in _F_STEMS (ratio 5.8×
        would otherwise fire)."""
        result, _ = normalizer.normalize_word_full("effulget", apply_pass2=True)
        assert result == "effulget"
