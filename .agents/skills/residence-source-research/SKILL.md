---
name: residence-source-research
description: Collect and audit original sources for the Poland Residence Observatory, including official residence, court, staffing and public-information statistics. Use for a new source, a factual correction or a dataset inventory.
---

Read `AGENTS.md` and the existing source register. Follow the claim from secondary coverage to the original agency publication or document. Prefer Sejm APIs, UdSC, NSA, NIK and official statistical releases; a public copy of a letter must keep that provenance label.

For each source record publisher, exact URL, document date, retrieval time, SHA-256, page/table/cell, licence, metric population and extraction status. Keep raw snapshots outside the repo. Inventory cited sources even when not parsed; distinguish inaccessible, catalog-only and extracted material.

Find contradictions by date, permit type and stage before treating them as errors. Check whether a number concerns pending cases, concluded cases, incoming applications, persons, plastic cards or staff FTE. Ask for definitions through a documented public-information request plan; do not send a request without user authorization.

Write evidence and proposed wording in `research/`. Explain the gaps and candidate official sources. Pass accepted observations to the data engineer and claims to a separate verifier. Do not silently promote secondary calculations to primary administrative facts.
