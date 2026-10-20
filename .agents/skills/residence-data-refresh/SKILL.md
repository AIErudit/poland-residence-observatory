---
name: residence-data-refresh
description: Acquire, normalize and reconcile aggregate residence-proceeding data for this observatory. Use when updating observations, adding a series or checking definition changes.
---

Read `AGENTS.md`, `data/curated/definitions.json` and the update instructions. Use `scripts/update_data.py` to stage snapshots outside the repo. Review differences before accepting data; acquisition never authorizes publication.

Preserve source IDs, locator, unit, as-of date, reference period, permit type, stage, denominator and comparability group on every observation. Keep stable project geography IDs from the existing dictionary (for example PL-DS and PL-MZ); map official TERYT codes separately if needed. Missing is not zero. Never pool different stock dates or calculate a national mean from regional means without valid weights.

Reconcile region sums and outcome partitions; reproduce derived shares from referenced numerator/denominator observations. Check method changes such as MOS/CUKR before a time-series comparison. Keep scenarios separate from observed data.

Run dataset tests and regenerate the dataset and CSV exports. Send the changed observation IDs, source hashes and reconciliation output to an independent verifier. Update the public site only after blocking findings are resolved.
