# Changes

## 2026-10-20 — deletion-receipt reset protection

Prevented New case / reset from reopening the form while a deletion receipt remains on this device. The control is disabled and its handler independently refuses the reset; the receipt must first be explicitly cleared through the existing control. Eight isolated Chromium/WebKit checks compare the published baseline with the fix at mobile and desktop widths, using a synthetic receipt and sending no submissions or deletions. Administrative observations and the running backend are unchanged.

## 2026-10-20 — v1.1.0, second research round

Replaced the Russian interface with Belarusian and added English; PL/BE/EN now cover main data, fact pages, survey and privacy. Added office trends, source-linked tables, separately reviewed Eurostat first-permit context, explicit Głos Migranta provenance and comparison, banking analysis for Millennium/PKO BP/Bank Pekao, and practical complaint/help routes.

Added a private Cloudflare Worker/D1 survey, mandatory server-side Turnstile validation, separate optional encrypted contact, stored versioned consent, idempotent receipts, self-service deletion and daily retention cleanup. Public survey publication remains review-gated.

All 1,780 core numeric values remain unchanged. Corrected the generic concluded-duration definition: MSWiA18089 does not expressly define the starting event, unlike the UdSC letter. Recorded unexplained one-case differences at WSA annual table boundaries. Added 15 separate Eurostat context observations; these are not waiting-time measurements. Preserved copies/reconstructed-label/system-break limitations and the unexplained 445458 forecast-prose versus 445462 CSV/API discrepancy.


## 2026-10-20 — initial research release

Normalized residence-proceeding statistics with explicit dates, definitions and source locators; published source inventory, reproducible calculations, independent AI verification scope, interactive tables, citation pages and a scenario calculator. This is a snapshot of historical source documents, not a live count.
