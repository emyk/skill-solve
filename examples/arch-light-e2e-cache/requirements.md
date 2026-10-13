# Requirements (ARCH, light depth)
- HARD: a product saved by `save_product` (in this process or another process on the same machine) is visible to the next `find_product`; never serve stale data after a save.
- HARD: stdlib only; `find_product`/`save_product`/`load_catalog` signatures unchanged; existing tests pass.
- SOFT: repeated `find_product` calls don't re-parse the file when nothing changed.
Criteria: correctness of invalidation 45 · simplicity 35 · lookup speed 20
