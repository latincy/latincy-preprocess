# Bug report: U/V normalizer flips vocalic `u` in the `vidu-` stem (viduatas → vidvatas)

**Package:** `latincy-preprocess` **0.3.1**
**Component:** `UVNormalizerRules` (`src/latincy_preprocess/uv/_rules.py`, Rule 10 `post_consonant_before_vowel`)
**Reported:** 2026-07-01
**Severity:** Medium — silently mangles a real Latin stem into a non-word; same *stem-not-in-list* class as the long-s allowlist bug.

## Summary

The `vidu-` stem (widow / deprive family: *vidua* "widow", *viduus*, *viduo*, *viduatus/-a/-as*) has a **vocalic** `u` in the `d-u-a/o` position. The normalizer classifies it as consonantal and rewrites `u → v`, producing non-words: `viduatas → vidvatas`.

## Reproduction

```python
from latincy_preprocess.uv import UVNormalizerRules
n = UVNormalizerRules()
for w in ["viduatas", "viduata", "vidua", "viduus", "viduo", "viduavit"]:
    print(w, "->", n.normalize(w))
```

| input | output | should be | rule fired |
|---|---|---|---|
| `viduatas` | `vidvatas` ❌ | `viduatas` | `post_consonant_before_vowel` |
| `viduata`  | `vidvata`  ❌ | `viduata`  | `post_consonant_before_vowel` |
| `vidua`    | `vidva`    ❌ | `vidua`    | `post_consonant_before_vowel` |
| `viduus`   | `vidvus`   ❌ | `viduus`   | `double_u_first_VCuu` |
| `viduo`    | `vidvo`    ❌ | `viduo`    | `post_consonant_before_vowel` |
| `viduavit` | `vidvavit` ❌ | `viduavit` | `post_consonant_before_vowel` |

Correctly handled siblings (already covered by stem list): `individua`, `residua`.

## Root cause

`vidu-` is missing from `_VOCALIC_U_STEMS` (`_rules.py:300`). In the `C-u-V` position (`d-u-a`), Rule 10 defaults to consonantal `v` unless a vocalic-u stem matches. The list already contains the structurally identical `individu`, `residu`, `assidu`, `strenu`, `conspicu`, etc. — `vidu` was simply never added. (The `viduus` case falls through Rule 5's double-u branch `double_u_first_VCuu`, which likewise checks `_VOCALIC_U_STEMS` and so is fixed by the same addition.)

## Suggested fix

Add `"vidu"` to `_VOCALIC_U_STEMS`:

```python
"vidu",  # vidua, viduus, viduo, viduatus (widow / deprive) — vocalic u
```

Then add regression cases (`viduatas`, `vidua`, `viduus`) to `tests/test_uv_rules.py`.

### Substring-collision check

`_VOCALIC_U_STEMS` matches via `if vocalic_stem in word_lower`, so verify `"vidu"` as a substring only ever appears where the `u` is genuinely vocalic before adding. Quick scan of common vocabulary:
- `individu-`, `residu-` — already vocalic (no change / same result).
- `providus/provida/provideo` — the relevant `u` here is `-dus`/before a consonant (Rule 8) or the intervocalic `provide-` `v`; the literal substring `vidu` does not occur in their u-only input (`prouid-`), so no collision.

No false-positive candidates found, but confirm against the full test corpus before release.
