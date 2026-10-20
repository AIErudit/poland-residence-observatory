# Private survey service

The public GitHub Pages site calls an isolated Cloudflare module Worker. The Worker uses a dedicated D1 database created with **EU jurisdiction**, prepared SQL, mandatory server-side Turnstile validation (hostname and action included), body/schema limits, idempotent receipts, short-lived abuse buckets, and separate encrypted optional contact storage. Application code does not log payloads. Deployment requests disabled Worker observability; API readback reports it as unconfigured (`null`), while Logpush is explicitly false. Database locality does not constrain every edge request or provider metadata to the EU.

Controller: **Vitali Bibikov**. Public contact: **support@pagefabrica.com**. Notice and consent version: `2026-10-20`. Response consent and separate email consent have stored timestamps and notice versions. Public notice source: `site/privacy-content.json`.

No raw response, email, receipt secret or individual narrative belongs in this repository, Issues, CI logs or a public chart. The survey collects no free text or files. Participation and every optional field are voluntary; it is not a representative sample or an official complaints channel.

## Deployment

The existing deployment uses purpose-specific credentials in the owner's private Site Factory credential system, with its canonical secret store. The normal factory identity resolves them; source/bootstrap tokens must not be changed. The purpose token is valid until **20 October 2027** and has Workers Scripts Write, D1 Write, Turnstile Sites Write and Account Settings Read on the owning account. Cloudflare's account-scoped APIs do not isolate these permissions to one script; operational commands must name only this service and its dedicated database. No DNS or registrar permissions were added to the purpose token. The original factory token was not modified.

For another account, copy `wrangler.example.jsonc` to ignored `wrangler.jsonc`, provision an EU-jurisdiction D1 database, apply `schema.sql`, and create a managed Turnstile widget restricted to the site's hostname. Set `TURNSTILE_SECRET`, `ADMIN_TOKEN` (random), `CONTACT_KEY` (32 random bytes, base64url), and `RATE_SECRET` as Worker secrets. Keep the plaintext credentials outside the public working tree and off the command line. The public **sitekey** is not the Turnstile secret; only the sitekey belongs in `site/survey-config.json`.

Deploy with `COLLECTION_ENABLED=false`. Check bindings, schema, disabled observability and daily cron `17 3 * * *`; verify `/health`, bad-token rejection, unauthenticated-export rejection and zero unintended records. Review UI, privacy notice and code with the separate verifier before setting `COLLECTION_ENABLED=true`. Updates must preserve secret bindings. Do not turn a test key or hostname bypass on in production. No paid tier, new domain or account plan change is required by this implementation, and none was activated for it.

## API and operator workflow

* `GET /health`: public schema/collection status only.
* `POST /v1/responses`: validated JSON + consent + Turnstile token. The browser creates `request_id` and a 32-byte `deletion_token` before sending, retaining only that receipt locally. Identical retries return the original receipt; different content with the same receipt conflicts. A successful commit followed by a lost response does not require a second row.
* `POST /v1/delete`: receipt id/token; removes the response and linked contact from the active database. The receipt is not a public share link.
* `GET /admin/export`: separate bearer secret, capped at 1,000 rows, no emails or deletion secrets. It returns private case data: use a local restricted file, never a browser URL or a CI artifact. Larger exports and contact access require an explicit private operator database query. Ciphertext contacts remain in a separate table; decrypt only for the consented follow-up with the private key.

Before analysing a response, check its coherence and duplicate signals and set `review_status='accepted'` or `'excluded'` in the private operator workflow. Similar region/month/permit combinations are not enough to collapse different people's cases. Turnstile does not prove one person or one case. For a correction, participants can delete and resubmit; there is no in-place public edit endpoint.

`scripts/aggregate_survey.py` reads a **private** export, accepts only operator-reviewed rows, separates pending from concluded cases and produces a candidate outside the public tree. It does not publish. A reviewer must check suppression, consent, provenance, missingness and selection bias before a release; `n>=10` is a disclosure floor, not statistical representativeness. Exact dates, individual rows and emails never go into published aggregates. No survey statistics are published in v1.1.0.

## Retention and recovery

Response expiry: 730 days; encrypted contact expiry: 180 days. A daily cron deletes expired rows and abuse buckets. A record can remain until the next daily cleanup. Rate identifiers use HMAC of IP and a ten-minute window; raw IP is not stored by this application. Cloudflare still handles network metadata under its own policies. D1 Time Travel history is always on and persists up to 7 days on Free / 30 days on Paid; do not promise immediate erasure from recovery history.

Do not restore a backup into collection without reapplying subsequent deletion requests and expiries. Use a temporary recovery copy and a private, minimal deletion ledger if recovery is needed. The prototype has no unattended restore or public export workflow. Source snapshots and truly anonymised released aggregates follow a different retention policy from personal responses.

## Cost and boundaries

The static site uses GitHub Pages and a locally vendored MIT **Chart.js 4.5.1**; native form controls require no framework or paid dashboard. Chart values also have accessible tables. The API and database are a separate service, with no real-time feed of official statistics. Account plan, abuse and usage affect the bill; free allowances are not a guaranteed zero bill. Check Cloudflare's current [Workers](https://developers.cloudflare.com/workers/platform/pricing/), [D1](https://developers.cloudflare.com/d1/platform/pricing/) and [Turnstile](https://developers.cloudflare.com/turnstile/plans/) terms before scaling.

Turnstile works on GitHub Pages, but it protects form submission through server verification. It does not put the entire `github.io` site behind Cloudflare's proxy/WAF. A later owned domain can support that separate configuration. No custom domain was purchased.

Operator correspondence policy: review closed Residence Observatory support threads monthly and delete within 12 months of closure unless a documented statutory or specific legal-claims need requires longer, minimised retention. This is a manual mailbox duty, separate from the implemented database cron.
