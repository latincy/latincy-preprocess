# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.3.0] - 2026-06-11

### Added

- `betacode` submodule: convert TLG/Perseus-style Beta Code into polytonic Unicode Greek (NFC). New public API `beta_to_unicode()`, `BetaCodeReplacer`, and `is_betacode()` — a heuristic guardrail for segmenting/gating input, since `beta_to_unicode()` transliterates every ASCII letter and must not be run on Latin. Adapted from the Classical Language Toolkit (`cltk.alphabet.grc.beta_to_unicode`, MIT), ported off the `regex` dependency to the standard library so the package stays dependency-free; output verified equivalent against the upstream doctests. Includes a 40-case test suite (CLTK parity, sigma/capital/diacritic handling, corpus round-trip, and `is_betacode` detection).

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

[0.2.0]: https://github.com/latincy/latincy-preprocess/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/latincy/latincy-preprocess/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/latincy/latincy-preprocess/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/latincy/latincy-preprocess/releases/tag/v0.1.0
