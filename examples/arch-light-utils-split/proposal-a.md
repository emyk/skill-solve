# Proposal a — Simplest design: turn `utils.py` into a `utils/` package, one module per existing section

## Overview
The file already has six sections marked by comments, and every call between helpers stays inside its own section (slugify→normalize_whitespace, write_json→atomic_write→ensure_dir, safe_get→retry, require_fields→non_empty, money→round_cents). So each section becomes its own module, unchanged. A 7-line `__init__.py` re-exports everything, so `from .utils import x` keeps working and none of the 3 importers change. Nothing new is added: no base classes, no registry, no deprecation shims.

## Components
`shop/utils/` replaces `shop/utils.py`:
- `text.py` (`re`), `money.py`, `dates.py`, `io.py` (`json, os`), `http.py` (`time`), `validation.py`. Function bodies are copied word for word, and each module imports only the stdlib it uses.
- `__init__.py`: `from .text import *` … one line per module.
- No module imports another sibling module.

## Migration path
1. Create the 6 modules by cutting at the `# --- group ---` markers, then delete `utils.py`.
2. Add `__init__.py` with the re-exports.
3. Run `pytest`. New code imports from `shop.utils.money` and so on. Moving existing importers to those paths is optional and can happen later.

## Risks and trade-offs
- Anything that patches `shop.utils.round_cents` will no longer affect callers inside `money`. I found no such patching today, since tests only cover the public cart and catalog behaviour.
- `import *` also re-exports names like `re` and `json`. That is harmless, and the old module exposed them too. The unused `csv`, `date`, `datetime`, `urlencode` and `parse_qs` imports are dropped.
- The re-export means callers are never forced onto the narrower paths, so the boundaries are clear in the layout but not enforced at call sites.

## Effort
About 15 minutes. 1 file removed, 7 added, 0 importers touched.

## Confidence
High. I spiked it in `a/scratch/w` with a scripted split: 2/2 tests pass, all 36 functions are reachable via `shop.utils`, and `cart`, `catalog` and `sync` all import.
