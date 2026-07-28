# Bug report: install fails on Python 3.14 (PyO3 0.23 cannot build against CPython 3.14)

**Package:** `latincy-preprocess` **0.3.2** (and all earlier releases)
**Component:** native build / packaging (`rust/Cargo.toml` PyO3 pin, `pyproject.toml` `requires-python`, `.github/workflows/release.yml` wheel matrix)
**Reported:** 2026-07-28
**Severity:** High — the package (and everything downstream: `latincy-vocab`, the `la_core_web_*` models) is uninstallable on CPython 3.14 on any platform without a matching prebuilt wheel; the failure surfaces as a cryptic Rust build error, not a clear "unsupported Python."
**Status:** Fixed in **0.3.3** (PyO3 0.25 + abi3 wheels + `requires-python <3.15`).

## Summary

A colleague installing `latincy-vocab` on macOS/CPython **3.14** hit a wheel build
failure deep in `latincy-preprocess`. Root cause: **PyO3 0.23.5 refuses to compile
against any CPython newer than 3.13.** Because no 3.14 wheel exists, pip falls back
to a source build, which fails the PyO3 version gate — regardless of whether a Rust
toolchain is present.

## Reproduction

```bash
# On CPython 3.14, force the source build that pip falls back to:
uv pip install --no-binary latincy-preprocess "latincy-preprocess==0.2.0"
```

Terminal output (abridged), reproduced 2026-07-28 on macOS arm64 / CPython 3.14.6:

```
error: the configured Python interpreter version (3.14) is newer than
       PyO3's maximum supported version (3.13)
  = help: please check if an updated version of PyO3 is available.
Current version: 0.23.5
  = help: set PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 to suppress this check ...
💥 maturin failed
```

## Why it presents as a confusing "Rust build" error rather than "unsupported Python"

The chain that turns "3.14 is unsupported" into a cryptic compiler failure:

1. The colleague installs `latincy-vocab` (`requires-python >=3.11`, **no upper
   cap**), which depends on `latincy-preprocess>=0.2.0` (**no upper cap**).
2. The current `latincy-preprocess` 0.3.2 declares `requires-python <3.14`, so pip
   on 3.14 **cannot** use it and **backtracks** to older releases seeking one that
   permits 3.14.
3. It lands on the uncapped `latincy-preprocess` 0.2.0 (`requires-python >=3.10`),
   which has no cp314 wheel, so pip builds its **sdist**.
4. The sdist build runs PyO3 0.23's build script, which hard-errors on CPython 3.14.

So the user sees a maturin/cargo failure instead of "requires Python 3.11–3.13."
Having Rust installed does **not** help — the failure is a version gate, not a
missing toolchain. (Verified: a machine with `cargo 1.92.0` on PATH fails at the
identical gate.)

## Scope across the dependency chain (verified 2026-07-28)

| Artifact | Python gate | Pin on preprocess | Needs a change? |
|---|---|---|---|
| `latincy-preprocess` | `requires-python <3.14`; PyO3 0.23 caps at 3.13 | — | **Yes** (the only fix) |
| `latincy-lexicon` 0.9.0 | `>=3.11` (open), pure Python | none | No |
| `latincy-vocab` 0.1.0 | `>=3.11` (open) | `>=0.2.0` (open) | No for 3.14; see note |
| `la_core_web_*` model wheels | **no `Requires-Python`** | `>=0.2.0,<0.4.0` | No (ceiling admits 0.3.3) |

`latincy-preprocess` is the **only** artifact in the chain that gates on the Python
version; everything upstream is pure-Python/data. The model's `<0.4.0` ceiling is
why the fix must ship in the **0.3.x** line.

## Fix (shipped in 0.3.3)

1. **PyO3 0.23 → 0.25** (first release to support CPython 3.14). No source changes
   were needed; the extension compiles unchanged and passes 621/621 parity+rules
   tests on CPython 3.11, 3.12, 3.13, and 3.14.
2. **abi3 wheels** (`abi3-py310`): one stable-ABI wheel per platform loads on
   3.10+ and on future CPythons with no rebuild — permanently ending the
   "new Python → no wheel → source build fails" recurrence. Verified: a single
   `cp310-abi3` wheel built on 3.11 installs and passes parity tests on 3.14.
3. **`requires-python` → `<3.15`**, plus a `Python :: 3.14` classifier.
4. Kept at **0.3.3** (not 0.4.0) so the model wheels' `<0.4.0` pin still resolves
   it without a model re-release.

## Recommended follow-ups (not in this package)

- **`latincy-vocab`**: importing it imports spaCy, which fails with
  `ModuleNotFoundError: No module named 'click'` under recent `typer` (spaCy's CLI
  imports click; newer typer no longer pulls it in). Add `click` to vocab's
  runtime deps (or pin typer) so a fresh install imports cleanly. Affects all
  Python versions, not just 3.14.
- **Resolver-trap hygiene**: the uncapped legacy releases (`latincy-preprocess`
  0.1.x–0.2.0) are what let pip backtrack into a doomed source build. Once 0.3.3
  with abi3 wheels is published the 3.14 trap is gone, but yanking or capping the
  oldest uncapped releases would make any *future* unsupported-Python install fail
  honestly ("requires Python …") instead of cryptically.
