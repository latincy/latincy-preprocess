<p align="center">
  <img src="https://raw.githubusercontent.com/latincy/latincy-preprocess/main/assets/latincy-preprocess-logo.jpg" alt="LatinCy Preprocess" width="600">
</p>

<p align="center">
  <a href="https://pypi.org/project/latincy-preprocess/"><img src="https://img.shields.io/pypi/v/latincy-preprocess.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/latincy-preprocess/"><img src="https://img.shields.io/pypi/pyversions/latincy-preprocess.svg" alt="Python versions"></a>
  <a href="https://github.com/latincy/latincy-preprocess/actions/workflows/ci.yml"><img src="https://github.com/latincy/latincy-preprocess/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
</p>

Latin text preprocessing: U/V normalization, long-s OCR correction, diacritics stripping, macron removal, and Beta Code → Unicode Greek conversion — plus Ancient Greek elision/accent normalization — with optional Rust acceleration and spaCy integration.

Consolidates [latincy-uv](https://github.com/diyclassics/latincy-uv) and [latincy-long-s](https://github.com/diyclassics/latincy-long-s) into a single package.

## Installation

```bash
pip install latincy-preprocess
```

For spaCy pipeline components:
```bash
pip install "latincy-preprocess[spacy]"
```

For Ancient Greek normalization:
```bash
pip install "latincy-preprocess[grc]"
```

For both:
```bash
pip install "latincy-preprocess[spacy,grc]"
```

(The quotes matter in zsh — the default shell on macOS — which otherwise
treats the brackets as a glob pattern and fails with `no matches found`.)

## Quick Start

```python
from latincy_preprocess import normalize

normalize("Gallia eft omnis diuisa in partes tres")
# 'Gallia est omnis divisa in partes tres'
```

## Per-Normalizer Usage

### U/V Normalization

Converts u-only Latin spelling to proper u/v distinction using rule-based analysis:

```python
from latincy_preprocess import normalize_uv

normalize_uv("Arma uirumque cano")
# 'Arma virumque cano'
```

Rules handle digraphs (*qu*), trigraphs (*ngu*), morphological exceptions (*cui*, *fuit*), positional context (initial, intervocalic, post-consonant), and case preservation.

### Long-S OCR Correction

Corrects OCR errors where historical long-s (ſ) was misread as *f*, using n-gram frequency analysis from Latin treebank data:

```python
from latincy_preprocess import LongSNormalizer

normalizer = LongSNormalizer()

word, rules = normalizer.normalize_word_full("ftatua")
# ('statua', [TransformationRule(...)])

text = normalizer.normalize_text_full("funt in fundamento reipublicae ftatua")
# 'sunt in fundamento reipublicae statua'
```

Two-pass strategy: Pass 1 applies high-confidence rules (impossible bigrams like *ft*, *fp*, *fc*). Pass 2 uses 4-gram frequency disambiguation for ambiguous word-initial *f-* patterns.

### Diacritics and Macrons

```python
from latincy_preprocess import strip_diacritics, strip_macrons

strip_macrons("ārma")
# 'arma'

strip_diacritics("λόγος")
# 'λογος'
```

### Beta Code → Unicode Greek

Latin prose corpora often encode embedded Greek quotations as TLG/Perseus-style Beta Code. Convert it to polytonic Unicode (NFC):

```python
from latincy_preprocess import beta_to_unicode

beta_to_unicode("zei/dwros a)/roura")
# 'ζείδωρος ἄρουρα'
```

Note: this transliterates *every* ASCII letter to Greek, so apply it only to isolated Beta Code spans, not mixed Latin/Greek text. Use `is_betacode()` to guard or segment input:

```python
from latincy_preprocess import beta_to_unicode, is_betacode

span = "a)/nqrwpos"
clean = beta_to_unicode(span) if is_betacode(span) else span
# 'ἄνθρωπος'  —  Latin spans are left untouched
```

`is_betacode()` is a heuristic (Beta Code written with no diacritics is indistinguishable from Latin), but it reliably catches accented Greek and ignores ordinary Latin punctuation.

### Ancient Greek Normalization

Requires the `grc` extra (`pip install latincy-preprocess[grc]`), which pulls in [`greek-normalisation`](https://github.com/jtauber/greek-normalisation).

Canonicalizes Ancient Greek for consistent tokenization and dictionary lookup — collapsing the many treebank/corpus encodings of the elision apostrophe to a single codepoint (U+2019), stripping lexicographic macron/breve marks, and folding grave → acute for lemma matching:

```python
from latincy_preprocess.grc import (
    normalize_surface,
    normalize_norm,
    normalize_lookup_key,
    is_greek_word,
)

# Surface form: NFC + canonical elision apostrophe (U+2019)
normalize_surface("μυρίʼ")     # 'μυρί’'   (Tesserae U+02BC → U+2019)
normalize_surface("ἀλλ'")      # 'ἀλλ’'    (ASCII apostrophe → U+2019)

# NORM: restore closed-class elision, grave → acute, movable nu/sigma
normalize_norm("δʼ")           # 'δέ'
normalize_norm("ἀλλ’")         # 'ἀλλά'

# Lookup key: grave → acute + final-sigma folding for dictionary matching
normalize_lookup_key("φονὸς")  # 'φονός'
normalize_lookup_key("λογοσ")  # 'λογος'

# Guard: Greek letters + the canonical elision mark only
is_greek_word("μυρί’")         # True
is_greek_word("anthropos")     # False
```

Consolidates the previously independent normalization implementations across the LatinCy Greek pipelines into a single source of truth for the elision/accent standard.

## spaCy Integration

Three pipeline components are available as spaCy factories:

### Unified Preprocessor (recommended)

Chains long-s correction → U/V normalization in the correct order:

```python
import spacy

nlp = spacy.blank("la")
nlp.add_pipe("latin_preprocessor")

doc = nlp("Gallia eft omnis diuisa in partes tres")
doc._.preprocessed          # 'Gallia est omnis divisa in partes tres'
doc[2]._.preprocessed       # 'est'
doc[2]._.preprocessed_lemma # normalized lemma
```

Either normalizer can be disabled:

```python
nlp.add_pipe("latin_preprocessor", config={"uv": False})
nlp.add_pipe("latin_preprocessor", config={"long_s": False})
```

### Standalone Components

```python
nlp.add_pipe("uv_normalizer")
# doc._.uv_normalized, token._.uv_normalized, token._.uv_normalized_lemma

nlp.add_pipe("long_s_normalizer")
# doc._.long_s_normalized, token._.long_s_normalized
```

## Rust Backend

When compiled with maturin, a Rust backend provides ~3x throughput for both normalizers. The backend is selected automatically:

```python
from latincy_preprocess import backend

backend()  # 'rust' or 'python'
```

The Python backend is fully functional and used as the fallback.

## Accuracy

### U/V Normalization

| Dataset | Accuracy |
|---------|----------|
| Curated test set (100 sentences) | 100% |
| UD Latin PROIEL (~21K u/v chars) | ~98% |
| UD Latin Perseus (~18K u/v chars) | ~97% |

### Long-S Correction

Pass 1 rules have a 0.00% false positive rate. Pass 2 disambiguation uses a protected allowlist of ~170 common Latin *f-* words (inline in `long_s/_rules.py`) plus n-gram frequency tables (JSON files in `long_s/data/ngrams/`).

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.

## Citation

```bibtex
@software{latincy_preprocess,
  title = {latincy-preprocess: Text Preprocessing for LatinCy Projects},
  author = {Burns, Patrick J.},
  year = {2026},
  url = {https://github.com/latincy/latincy-preprocess}
}
```

## Acknowledgments

The `betacode` submodule adapts the Beta Code → Unicode conversion tables and algorithm from the [Classical Language Toolkit](https://github.com/cltk/cltk) (`cltk.alphabet.grc.beta_to_unicode`), used under the MIT License (Copyright © 2013 Classical Language Toolkit). It is reimplemented here on the Python standard library so the package remains dependency-free.

The `grc` submodule is built on James Tauber's [`greek-normalisation`](https://github.com/jtauber/greek-normalisation).

## License

MIT
