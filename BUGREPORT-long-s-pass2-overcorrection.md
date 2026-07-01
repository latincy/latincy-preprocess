# Bug report: long-s Pass-2 over-corrects common f-words (allowlist incomplete + not stem-aware)

**Package:** `latincy-preprocess` **0.3.1** (PyPI wheel)
**Component:** `LongSNormalizer.normalize_word_full(..., apply_pass2=True)` (long-s OCR correction, Pass 2 — context-dependent f→s)
**Reported:** 2026-06-30 (surfaced during latincy-pretrain D3 corpus-correction QA)
**Severity:** **High** for corpus-cleaning use — at scale it injects "real-but-wrong word" errors into training data (the COPIA failure mode), and it currently **blocks** the latincy-pretrain D3 corrected re-run / threshold selection.

## Summary

Pass-2 long-s correction is simultaneously **too aggressive** (flips `f→s` in common, correct Latin words) and **not aggressive enough** (misses real long-s in `-ff-` / `-nf-` contexts). Root cause: the **runtime allowlist contains only 160 words** (vs the ~4,500 attested f-words the design/README describes), and it is **word-exact, not stem-aware** — so derivatives and common vocabulary fall through to the over-eager 4-gram heuristic.

## Reproduction

```python
# pip install latincy-preprocess==0.3.1
from latincy_preprocess import LongSNormalizer
n = LongSNormalizer()
for w in ["infelix", "felicitas", "fere", "festus", "accenfus", "Gloffario"]:
    out, rules = n.normalize_word_full(w, apply_pass2=True)
    print(w, "->", out)
```

### False positives — correct Latin wrongly altered (4 / 20 common f-words probed)

| input | output | should be | in allowlist? |
|---|---|---|---|
| `infelix` | `inselix` ❌ | `infelix` | absent (`felix` IS present) |
| `felicitas` | `selicitas` ❌ | `felicitas` | absent |
| `fere` | `sere` ❌ | `fere` | absent |
| `festus` | `sestus` ❌ | `festus` | absent |

Preserved correctly (16/20): felix, ferre, fero, filius, facere, fides, finis, forma, fortis, frater, fugere, ferrum, fama, facile, fluvius, flos.

### False negatives — real long-s OCR errors missed

| input | output | should be | unhandled pattern |
|---|---|---|---|
| `accenfus` | `accenfus` ❌ | `accensus` | medial `-nf-` (→ `-ns-`) |
| `Gloffario` | `Gloffario` ❌ | `Glossario` | medial `-ff-` (→ `-ss-`) |

(High-confidence cases work correctly: `fenatus→senatus`, `quafi→quasi`, `noftro→nostro`, `eft→est`.)

## Root cause

1. **Runtime allowlist is truncated.** `tests/data/allowlist.json` ships **160 entries**; the README describes a ~4,500-word attested-f-word allowlist. Either the full list isn't packaged in the 0.3.1 wheel, or the runtime path reads a fixture-sized subset. Words absent from the list fall through to the Pass-2 4-gram frequency heuristic, which flips `f→s` whenever the `s`-form 4-grams are more frequent — breaking `infelix`, `felicitas`, `fere`, `festus`.
2. **Allowlist is word-exact, not stem-aware.** `felix` is protected but its derivative `infelix` is not; `ferre` is protected but `fere` is not. This is the *same* class of bug fixed for U/V in 0.3.1 — where the fix was to add **stems** to a vocalic-u stem list. Long-s needs the analogous treatment.
3. **Pass-2 rule set omits `-ff-` and `-nf-` long-s contexts**, so genuine early-modern long-s in those clusters is never corrected.

## Suggested fixes (in rough priority)

1. **Package + load the full ~4,500-word allowlist** at runtime (confirm the wheel includes it, not just the 160-word test fixture).
2. **Make the allowlist stem-aware** (mirror the 0.3.1 U/V stem-list fix): protect `fel-`, `fer-`/`fere`, `fest-`, etc. so derivatives inherit protection.
3. **Add `-ff-`→`-ss-` and `-nf-`→`-ns-` (and similar medial) patterns** to Pass-2, guarded by the allowlist, to recover the missed corrections.
4. **Add regression tests** for the failing cases above — the README's "100% on 852 occurrences / 8 patterns" validation set evidently lacks common derivatives (infelix/felicitas/fere/festus) and the `-ff-`/`-nf-` contexts; extend the fixture with these.

## Immediate impact / decision needed (latincy-pretrain side)

D3 corpus correction is **paused** — re-running with 0.3.1 Pass-2 would mangle good Latin (e.g. `infelix→inselix`) and corrupt the bigram-coherence scores used to set the quality-filter threshold. Interim options until a fixed release:
- **(a)** ship a fixed `latincy-preprocess` (full + stem-aware allowlist) — preferred;
- **(b)** fall back to the validated sibling `latincy-long-s` if its allowlist is intact;
- **(c)** run **Pass-1 only** (high-confidence `fp/ft/fc/fqu`, ~0% FP) — safe but lower recall — to keep the pipeline moving.

Pass-1-only is the safe stopgap; the corpus-scale "correct" lever needs (a) or (b) before D1/D2.
