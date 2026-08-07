"""
Ancient Greek normalization rules: elision, accent folding, lookup keys.

Consolidates two previously independent, near-duplicate implementations —
latincy-grc-pipelines/scripts/functions.py (normalize_surface, normalize_norm,
the private _normalize_greek used by its lemmatizer) and latincy-grc-words'
scripts/utils/normalize.py (normalize_greek_accents, normalize_final_sigma,
is_greek_word) — into a single source of truth. See the LatinCy grc
normalization standard (latincy-grc-pipelines/.claude/CLAUDE.md) for the full
rationale: Perseus/PROIEL/GLAUx/PTNK each encode the elision apostrophe
differently, which silently breaks tokenization and elision-lemma resolution
unless every consumer normalizes identically.

Canonical form:
  - NFC.
  - Elision apostrophe = U+2019 (RIGHT SINGLE QUOTATION MARK); U+0027, U+02BC,
    U+1FBF, and dangling combining U+0313 all map to it.
  - Macrons/breves (U+0304/U+0306) stripped — lexicographic vowel-length
    marks, not real Ancient Greek orthography.
  - No dangling combining marks.

Built on James Tauber's `greek-normalisation` (https://github.com/jtauber/greek-normalisation).
"""

from __future__ import annotations

import functools
import unicodedata
from typing import Dict

from greek_normalisation.normalise import Norm as _GNNorm
from greek_normalisation.normalise import Normaliser as _GNNormaliser
from greek_normalisation.utils import convert_to_2019 as _gn_to2019
from greek_normalisation.utils import nfc as _gn_nfc

# ----- grave (VARIA) -> acute (OXIA) mapping, for lookup-key folding ----- #
# Union of the two tables independently maintained before this consolidation;
# the "standalone accent marks" entries (U+1FCD/1FDD/1FED/1FEF) existed only
# in latincy-grc-words' copy, not latincy-grc-pipelines'.
GRAVE_TO_ACUTE: Dict[str, str] = {
    # Alpha with breathing
    "ἂ": "ἄ", "ἃ": "ἅ",
    "Ἂ": "Ἄ", "Ἃ": "Ἅ",
    # Epsilon
    "ἒ": "ἔ", "ἓ": "ἕ",
    "Ἒ": "Ἔ", "Ἓ": "Ἕ",
    # Eta
    "ἢ": "ἤ", "ἣ": "ἥ",
    "Ἢ": "Ἤ", "Ἣ": "Ἥ",
    # Iota
    "ἲ": "ἴ", "ἳ": "ἵ",
    "Ἲ": "Ἴ", "Ἳ": "Ἵ",
    # Omicron
    "ὂ": "ὄ", "ὃ": "ὅ",
    "Ὂ": "Ὄ", "Ὃ": "Ὅ",
    # Upsilon
    "ὒ": "ὔ", "ὓ": "ὕ", "Ὓ": "Ὕ",
    # Omega
    "ὢ": "ὤ", "ὣ": "ὥ",
    "Ὢ": "Ὤ", "Ὣ": "Ὥ",
    # Simple vowel + varia
    "ὰ": "ά", "ὲ": "έ", "ὴ": "ή",
    "ὶ": "ί", "ὸ": "ό", "ὺ": "ύ",
    "ὼ": "ώ",
    # With iota subscript
    "ᾂ": "ᾄ", "ᾃ": "ᾅ",
    "ᾊ": "ᾌ", "ᾋ": "ᾍ",
    "ᾒ": "ᾔ", "ᾓ": "ᾕ",
    "ᾚ": "ᾜ", "ᾛ": "ᾝ",
    "ᾢ": "ᾤ", "ᾣ": "ᾥ",
    "ᾪ": "ᾬ", "ᾫ": "ᾭ",
    "ᾲ": "ᾴ", "ῂ": "ῄ", "ῲ": "ῴ",
    # Capitals
    "Ὰ": "Ά", "Ὲ": "Έ", "Ὴ": "Ή",
    "Ὶ": "Ί", "Ὺ": "Ύ", "Ὸ": "Ό",
    "Ὼ": "Ώ",
    # Dialytika + varia
    "ῒ": "ΐ", "ῢ": "ΰ",
    # Standalone accent marks
    "῍": "῎",  # psili + varia -> psili + oxia
    "῝": "῞",  # dasia + varia -> dasia + oxia
    "῭": "΅",  # dialytika + varia -> dialytika + oxia
    "`": "´",  # varia -> oxia (standalone)
}
_GRAVE_TO_ACUTE_TABLE = str.maketrans(GRAVE_TO_ACUTE)

_COMBINING_GRAVE = "̀"
_COMBINING_ACUTE = "́"
_COMBINING_MACRON = "̄"
_COMBINING_BREVE = "̆"

# Conservative NORM config for normalize_norm: the orthographic unifications
# only (restore elision, grave->acute, movable nu/sigma, extra final accent).
# Deliberately excludes CAPITALISED / PROCLITIC / ENCLITIC so this doesn't
# lowercase proper nouns or drop enclitic accents.
_NORM_CONFIG = _GNNorm.GRAVE | _GNNorm.ELISION | _GNNorm.MOVABLE | _GNNorm.EXTRA
_NORMALISER = _GNNormaliser(config=_NORM_CONFIG)

# LatinCy-owned elision restoration overlay, consulted AFTER the library's
# ELISION map (greek_normalisation.norm_data.ELISION, 36 NT/MorphGNT-oriented
# entries) fails to fire. The library map has essentially no epic/tragic
# coverage — ἄρ’, κ’, θ’, ἔνθ’, μάλ’, οὔτ’, ἔπειτ’, μέγ’ etc. all fall through
# and previously leaked the elided surface as the "isolation form" (and from
# there, via the lookup_lemmatizer fallback, as the lemma; reported externally
# against Homer, where ἄρ’ alone is ~600 tokens).
#
# Values are the restored FORM IN ISOLATION (MorphGNT sense), not the lemma:
# μέγ’ -> μέγα (lemma μέγας), πόλλ’ -> πολλά (lemma πολύς). Enclitics restore
# unaccented, matching the library's own convention (ποτ’ -> ποτε, σ’ -> σε).
#
# Curation policy: only forms whose restoration is unambiguous. Mined from the
# normalized LatinCy grc treebanks (Perseus/PROIEL/PTNK/GLAUx), frequency floor
# ~200 gold tokens, plus the externally-reported Homer set. Deliberately
# EXCLUDED as ambiguous — do not add without evidence:
#   αὖθ’ (αὖτε/αὖθι), ἔστ’/ἔσθ’ (ἐστί/ἔστε), οἶδ’ (οἶδα/οἶδε),
#   αὐτ’ (αὐτό/αὐτά), κεῖν’ (κεῖνο/κεῖνα), Δί’ (Διί/Δία), τιν’ (τινά/τινί),
#   μυρί’ (μυρία/μυρίοι-vocalism uncertain), generic verb -ε/-ο elisions.
# Person/case-ambiguous forms that still share ONE lemma (οἶδ’, ἔφατ’, Δί’)
# belong in the latincy-grc-words lemma table as aliases, not here.
GRC_ELISION_EXTRA: Dict[str, str] = {
    # particles
    "ἄρ’": "ἄρα",
    "ἆρ’": "ἆρα",
    "ῥ’": "ῥα",
    "κ’": "κε",
    "θ’": "τε",       # aspirated before rough breathing
    "ς’": "σε",       # final-sigma encoding of σ’ (GLAUx artifact, 1k+ gold tokens)
    # negative/copulative conjunctions
    "οὔτ’": "οὔτε",
    "οὔθ’": "οὔτε",
    "μήτ’": "μήτε",
    "μήθ’": "μήτε",
    "ἠδ’": "ἠδέ",
    # subordinators
    "ὥστ’": "ὥστε",
    "ὥσθ’": "ὥστε",
    "ὅθ’": "ὅτε",
    # adverbs
    "ἔνθ’": "ἔνθα",
    "ἐνθάδ’": "ἐνθάδε",
    "μάλ’": "μάλα",
    "μάλιστ’": "μάλιστα",
    "μάλισθ’": "μάλιστα",
    "ἔπειτ’": "ἔπειτα",
    "ἔπειθ’": "ἔπειτα",
    "εἶθ’": "εἶτα",
    "τότ’": "τότε",
    "ποθ’": "ποτε",   # aspirated ποτ’; unaccented like the library's ποτ’ -> ποτε
    "οὐκέτ’": "οὐκέτι",
    "μηκέτ’": "μηκέτι",
    "τάχ’": "τάχα",
    "ὧδ’": "ὧδε",
    "δῆτ’": "δῆτα",
    "αὖτ’": "αὖτε",
    "ἅμ’": "ἅμα",
    "ἔγωγ’": "ἔγωγε",
    # prepositions (library covers ἀπ’/ἐπ’/κατ’/μετ’/παρ’/ὑπ’/δι’ + aspirates)
    "ἀντ’": "ἀντί",
    "ἀμφ’": "ἀμφί",
    # pronouns / demonstratives (-δε deictics restore the dropped ε)
    "τοῦθ’": "τοῦτο",
    "τόδ’": "τόδε",
    "τάδ’": "τάδε",
    "ὅδ’": "ὅδε",
    "τόνδ’": "τόνδε",
    "τήνδ’": "τήνδε",
    "τῷδ’": "τῷδε",
    "τῶνδ’": "τῶνδε",
    "τοῖσδ’": "τοῖσδε",
    "τούσδ’": "τούσδε",
    "τοιαῦτ’": "τοιαῦτα",
    "τοιαῦθ’": "τοιαῦτα",
    "τοσαῦτ’": "τοσαῦτα",
    "τοσαῦθ’": "τοσαῦτα",
    "ὅσ’": "ὅσα",
    "ὅς’": "ὅσα",     # final-sigma encoding, as with ς’
    # adjectives/quantifiers with unambiguous neuter restoration
    "μέγ’": "μέγα",
    "ἄλλ’": "ἄλλα",   # accented ἄ- : ἄλλος, never the conjunction ἀλλ(ά)
    "πόλλ’": "πολλά",
    "δύ’": "δύο",
}


@functools.lru_cache(maxsize=100_000)
def normalize_surface(text: str) -> str:
    """Canonical SURFACE form: NFC + a single elision codepoint (U+2019).

    Keeps the elided *form* (ἀλλ' stays ἀλλ') but forces the apostrophe to
    U+2019 and repairs punctuation, so all known treebank/corpus encodings
    collapse to one representation. U+0313->U+2019 is safe *after* macron/breve
    stripping and NFC recomposition: legitimate smooth breathings then compose
    onto their vowel, so any residual U+0313 is a genuinely dangling elision
    mark on a consonant.

    Macron/breve stripping MUST happen before the U+0313 check, not after:
    dictionary sources (Wiktionary) sometimes mark a vowel's length AND its
    breathing (ᾰ̓ = alpha + breve + breathing) — Unicode has no single
    codepoint for that combination, so the breathing is *always* left
    dangling by NFC alone, purely because the breve is in the way, not
    because it's elision. Stripping the breve first frees the breathing to
    recompose correctly (ᾰ̓ -> ἀ). Checking U+0313 first would misread that
    dangling-for-unrelated-reasons breathing as elision and corrupt the word
    (observed: ᾰ̓γγέλλω -> α’γγέλλω instead of ἀγγέλλω).
    """
    if not text:
        return text
    text = _gn_nfc(text)                     # NFC (composes legit breathings)
    text = _gn_to2019(text)                  # U+02BC, U+1FBF -> U+2019 (library)
    # Strip macrons/breves (vowel-length marks) and recompose BEFORE checking
    # for dangling U+0313, so breathings blocked only by a length mark compose
    # correctly instead of being mistaken for elision.
    text = unicodedata.normalize("NFD", text)
    text = text.replace(_COMBINING_MACRON, "").replace(_COMBINING_BREVE, "")
    text = unicodedata.normalize("NFC", text)
    text = text.replace("̓", "’")  # dangling combining elision -> U+2019
    text = text.replace("'", "’")  # ascii apostrophe -> U+2019
    text = text.replace("̅", "")        # strip stray combining overline
    return unicodedata.normalize("NFC", text)


@functools.lru_cache(maxsize=100_000)
def normalize_norm(text: str) -> str:
    """Canonical NORM: MorphGNT 'form in isolation'.

    Restores elision (ἀλλ'->ἀλλά, δ'->δέ), folds grave->acute and movable
    nu/sigma. Surface-normalises first (else ELISION can't fire — the
    `greek-normalisation` library only recognises elision when the
    apostrophe is already U+2019). Forms the library's NT-oriented ELISION
    map misses are restored via the LatinCy overlay ``GRC_ELISION_EXTRA``
    (epic/tragic coverage), including a titlecase fallback so line-initial
    capitalized elisions (Ἄρ’) restore too. Forms in neither map are
    returned elided, unchanged — this module must not guess ambiguous
    restorations (μυρί’, ἔστ’).
    """
    if not text:
        return text
    normed = _NORMALISER.normalise(normalize_surface(text))[0]
    if normed.endswith("’"):
        extra = GRC_ELISION_EXTRA.get(normed)
        if extra is None and normed[:1] != normed[:1].lower():
            lowered = normed[:1].lower() + normed[1:]
            restored = GRC_ELISION_EXTRA.get(lowered)
            if restored is not None:
                extra = restored[:1].upper() + restored[1:]
        if extra is not None:
            return extra
    return normed


def _fold_final_sigma(text: str) -> str:
    """Fold word-final medial sigma (σ) to final sigma (ς)."""
    result = list(text)
    for i, c in enumerate(result):
        if c == "σ" and (i == len(result) - 1 or not result[i + 1].isalpha()):
            result[i] = "ς"
    return "".join(result)


@functools.lru_cache(maxsize=100_000)
def normalize_lookup_key(text: str) -> str:
    """Canonical form for dictionary/lookup-table matching (not surface text).

    Running text takes grave accent on oxytone ultimas (φονός -> φονὸς); a
    lemma dictionary is keyed on the acute citation form. This folds
    grave->acute and final-sigma on top of ``normalize_surface`` (so it is
    also elision- and macron/breve-safe even for callers that never call
    normalize_surface first — e.g. raw extraction from a corpus).

    Replaces two independently-written, near-duplicate implementations of
    this same concern: latincy-grc-pipelines' former private
    ``_normalize_greek`` and latincy-grc-words' former
    ``normalize_greek_accents`` + ``normalize_final_sigma``.
    """
    if not text:
        return text
    result = normalize_surface(text)
    result = result.translate(_GRAVE_TO_ACUTE_TABLE)
    if _COMBINING_GRAVE in result:
        result = result.replace(_COMBINING_GRAVE, _COMBINING_ACUTE)
    result = unicodedata.normalize("NFC", result)
    return _fold_final_sigma(result)


def is_greek_word(text: str) -> bool:
    """Check if text contains only Greek letters and the canonical elision mark.

    Accepts polytonic Greek characters (base letters, accented letters,
    breathing marks) and the canonical elision mark (U+2019, per the grc
    normalization standard). Rejects text with Latin letters, digits, or
    non-Greek scripts.

    Without the U+2019 exception, every elided word (δ', ἀλλ', μυρί', ...)
    fails this check — which is exactly what silently excluded elision from
    the lemma lookup table before this fix (extraction filters call this
    before is_greek_word ever sees a canonicalized form).
    """
    if not text or len(text) > 50:
        return False

    for c in text:
        if c == "’":  # elision mark - not alphabetic, but valid AG orthography
            continue
        if c.isalpha():
            cp = ord(c)
            if not (
                (0x0370 <= cp <= 0x03FF)     # Greek and Coptic
                or (0x1F00 <= cp <= 0x1FFF)  # Greek Extended
            ):
                return False
        else:
            return False

    return True
