# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.4.0] - 2026-08-03

### Added

- **Ancient Greek (`grc`) normalization module** — the package's first
  non-Latin content. New public API `normalize_surface`, `normalize_norm`,
  `normalize_lookup_key`, `is_greek_word`, and the `GRAVE_TO_ACUTE` table
  (`from latincy_preprocess.grc import ...`). Consolidates three previously
  independent, partially-duplicated implementations across the LatinCy grc
  repos (latincy-grc-pipelines' `functions.py`/`_normalize_greek` and
  latincy-grc-words' `normalize.py`) into one source of truth for the grc
  normalization standard: elision apostrophe canonicalized to U+2019 (U+0027,
  U+02BC, U+1FBF, and dangling combining U+0313 all map to it), macron/breve
  stripping, grave→acute folding, and final-sigma folding for lookup keys.
- **New optional extra `grc`** (`pip install latincy-preprocess[grc]`) pulling
  in `greek-normalisation>=0.5.1`, on which the module is built.
- 27 tests (`tests/test_grc_rules.py`), including a parity check against the
  pre-consolidation latincy-grc-pipelines behavior for the Tesserae-style
  elision cases that motivated the work, and a regression test for a real
  corruption bug fixed here: a vowel marked with both length (breve) and
  breathing has no single precomposed codepoint, so NFC alone left the
  breathing dangling and it was mis-read as elision (`ᾰ̓γγέλλω` → `α’γγέλλω`
  instead of `ἀγγέλλω`); macron/breve stripping now runs before the
  dangling-U+0313 check.

### Changed

- Package description and keywords/classifiers updated to reflect Ancient Greek
  support (added `greek` keyword, `Natural Language :: Greek` classifier).

### Notes

- Additive only — zero changes to existing Latin functionality (U/V, long-s,
  betacode). Safe MINOR bump under semver.
- Published `la_core_web_*` models pin `latincy-preprocess>=0.2.0,<0.4.0`, so
  Latin-model installs continue to resolve to 0.3.3 and are unaffected. The grc
  module targets the grc-pipelines/grc-words consumers, which do not depend on
  the Latin core models; co-resolving the Latin models with the grc features in
  one environment requires those models to raise their upper bound in a future
  re-release.

## [0.3.3] - 2026-07-28

### Added

- **Python 3.14 support.** The extension now builds against PyO3 0.25 (up from
  0.23, which hard-capped at CPython 3.13 and made 3.14 installs fail in the
  Rust build with *"the configured Python interpreter version (3.14) is newer
  than PyO3's maximum supported version (3.13)"*). `requires-python` widened to
  `<3.15`.

### Changed

- **Wheels are now abi3** (stable ABI, `abi3-py310`): one wheel per platform
  (`cp310-abi3-*`) loads on CPython 3.10+ and on future CPython releases without
  a rebuild, replacing the per-version wheel matrix. This ends the recurring
  "new Python release has no wheel → pip falls back to a source build" failure,
  and as a side effect adds macOS wheels for 3.10–3.12 (macOS previously shipped
  a cp313 wheel only, forcing everyone else on macOS to compile from source).
- CI test matrix extended through 3.13 and 3.14.

### Notes

- No API or behaviour changes. 621 parity/rules tests pass unchanged on
  CPython 3.11, 3.12, 3.13, and 3.14.
- Kept on the 0.3.x line (not 0.4.0) deliberately: the published `la_core_web_*`
  models pin `latincy-preprocess>=0.2.0,<0.4.0`, so a 0.4.0 would be excluded and
  reintroduce the resolver backtracking failure. 0.3.3 resolves under that
  ceiling with no model re-release.

## [0.3.2] - 2026-06-30

### Fixed

- Long-S: `infelix`/`infelicis` and related compounds incorrectly converted to
  `inselix`/`inselicis` — added `'fel'` stem to `_F_STEMS` so the medial-f
  guard recognises the *felix/felicitas* family in prefix compounds.
- Long-S: word-initial *fe-* words (`felicitas`, `fere`, `festus`) incorrectly
  converted — added `_F_WORD_INITIAL_STEMS = ('fel', 'fest')` stem-prefix guard
  in Pass 2, replacing fragile word-exact entries; `fere` retained word-exact as
  it has no morphological family.
- Long-S: `accensus` OCR form `accenfus` not corrected — `'fus'` stem was too
  broad and matched word-final `-fus`; replaced with specific inflection stems
  (`'fusu'`, `'fuso'`, `'fusa'`, `'fusi'`, `'fusio'`).
- Long-S: `efulget` family (`effulget`, `affulgere`) incorrectly converted —
  added `'ful'` stem to `_F_STEMS`.
- Long-S: double-*f* → *ss* OCR pattern entirely unhandled (`Gloffario`,
  `claffis`, `miffus`, `paffus`, `neceffe`) — added 4-gram pre-scan in
  `_normalize_medial_f()` comparing `[prev]ff[next]` vs `[prev]ss[next]`
  frequency; `_F_STEMS` guard applied to the second-*f* tail to protect
  legitimate compounds (`offero`, `effulget`).
- Long-S: `poffe` not corrected to `posse` — `poff` has zero corpus presence
  and is phonologically impossible in Latin; added `poff → poss` as a Pass 1
  rule (alongside `ft`, `fp`, `fc`); applied before Rust backend so that
  `poffum → possum` rather than `pofsum`.

## [0.3.1] - 2026-06-26

### Fixed

- U/V: *mortuus* declined forms (*mortuo*, *mortuis*, *mortuos*, *mortuam*)
  misclassified as consonantal v — stem `mortu-` added to vocalic-u stem list.
- U/V: *tribuo* conjugated forms (*tribuebatur*, *tribuunt*, *tribuerant*)
  misclassified — stem `tribu-` added to vocalic-u stem list.
- U/V: *consuetudo*, *consuetudine* (and related *insuetus*, *desuetus*)
  misclassified — stem `suet-` added to vocalic-u stem list.
- U/V: *triduum*, *triduo* misclassified — stem `tridu-` added to vocalic-u
  stem list; Rule 5 double-u branch now checks vocalic-u stems before
  returning consonantal v (previously only Rule 10 checked them).
- U/V: 2sg/2pl perfect indicative (*adfuisti*, *fuisti*, *fuistis*, *potuisti*)
  misclassified — new `-uisti`/`-uistis` sub-rule added to Rule 4, restricted
  to `_U_PERFECT_CONSONANTS` to avoid false positives on consonant-stem
  i-perfects (*soluisti* from *solvo* correctly reaches Rule 10).
- U/V: pluperfect subjunctive (*floruisset*, *adfuisses*, *potuissem*,
  *potuissemus*, *potuissent*) misclassified — extended the `-uisse` Rule 4
  check to accept the full set of plupf.subj. personal endings, and restricted
  to `_U_PERFECT_CONSONANTS` (same guard as `-uisti`).
- U/V: 3pl perfect *-uerunt* forms (*debuerunt*, *habuerunt*, *potuerunt*,
  *fuerunt*) misclassified — `perfect_uer_stem` extended to include `-uerunt`
  (vowel `u` following `r` in the stem).
- U/V: r-stem u-perfect forms (*disseruit*, *aperuit*/*aperui*, *meruit*,
  *paruit*, *corruit*) misclassified — added as word exceptions in
  `_VOCALIC_U_WORDS`; the consonant-set approach was rejected because it
  creates false positives for *servit* → *seruit* (3sg present of *servio*).
- U/V: *voluisti*/*voluistis* (2sg/2pl perfect of *volo*) misclassified —
  extended the `volo_perfect` special case to cover `-uisti`/`-uistis` forms.
- U/V: compound pronouns (*alicuius*, *alicui*, *alicuique*, *unicuique*,
  *cuiusque*, *cuiuspiam*, *cuiuslibet*, *cuiusvis*) misclassified — added to
  `_VOCALIC_U_WORDS`.

All fixes applied to both Python and Rust backends (34 new regression tests).

## [0.3.0] - 2026-06-12

This release bundles the U/V enclitic fixes below with the new betacode submodule. The 0.2.1 fixes were developed but never published standalone; the 0.2.1 section is retained for provenance, and 0.3.0 carries everything to PyPI (last published: 0.2.0).

### Added

- `betacode` submodule: convert TLG/Perseus-style Beta Code into polytonic Unicode Greek (NFC). New public API `beta_to_unicode()`, `BetaCodeReplacer`, and `is_betacode()` — a heuristic guardrail for segmenting/gating input, since `beta_to_unicode()` transliterates every ASCII letter and must not be run on Latin. Adapted from the Classical Language Toolkit (`cltk.alphabet.grc.beta_to_unicode`, MIT), ported off the `regex` dependency to the standard library so the package stays dependency-free; output verified equivalent against the upstream doctests. Includes a 40-case test suite (CLTK parity, sigma/capital/diacritic handling, corpus round-trip, and `is_betacode` detection).

### Fixed

- U/V: remaining u-perfect rules with a word-end check now also accept a trailing `-que`/`-ne`/`-ve` enclitic and keep the u vocalic (extends the *implicuitque* fix from 0.2.1). Corrects *voluitque*, *noluitque*, *maluitque* (`volo_perfect`), *potuique* (`perfect_ui`), *potuimusne* (`perfect_uimus`), *potuisseque* (`perfect_uisse`), and *potuereque* (`perfect_uere`) — previously misread as *volvitque*, *potvique*, etc. Applied to both Python and Rust backends.

## [0.2.1] - 2026-05-28

### Fixed

- U/V: double-u before vowel misclassified — *Vesuuius* now correctly normalizes to *Vesuvius* (V-C-uu-V pattern).
- U/V: u-perfect forms with `-que` enclitic misclassified — *implicuitque* no longer becomes *implicvitque*; enclitic attachment now handled in perfect-tense rules (Python and Rust).
- U/V: *assiduis* (dative plural of *assiduus*) misclassified as *assidvis*; stem `assidu-` added to vocalic-u stem list.

## [0.2.0] - 2026-03-15

### Added

- Word-initial `fo→so` disambiguation using quadgram frequency analysis (e.g. *folus→solus*, *folet→solet*) while preserving legitimate f-words (*forum*, *forma*, *fortis*).
- Medial long-s detection: non-initial `f→s` correction using surrounding trigram evidence with f-stem protection for compound verbs (e.g. *obfecro→obsecro*, *abfens→absens*).

## [0.1.2] - 2026-02-24

### Fixed

- Word-initial C+u clusters (e.g. *puer* → *pver*) misclassified as consonantal v.

## [0.1.1] - 2026-02-01

### Fixed

- `strip_diacritics()` no longer lowercases text — now preserves original case. Lowercasing was an unintended side effect conflating two separate operations.

## [0.1.0] - 2026-01-26

### Added

- Initial release: U/V normalization, long-s OCR correction, diacritics stripping, macron removal, spaCy integration, optional Rust backend.

[0.4.0]: https://github.com/latincy/latincy-preprocess/compare/v0.3.3...v0.4.0
[0.3.0]: https://github.com/latincy/latincy-preprocess/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/latincy/latincy-preprocess/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/latincy/latincy-preprocess/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/latincy/latincy-preprocess/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/latincy/latincy-preprocess/releases/tag/v0.1.0
