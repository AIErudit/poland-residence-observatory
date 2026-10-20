PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS responses (
 id TEXT PRIMARY KEY, created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL,
 deletion_hash TEXT NOT NULL, submission_hash TEXT NOT NULL, schema_version INTEGER NOT NULL, payload TEXT NOT NULL,
 privacy_version TEXT NOT NULL, consent_at INTEGER NOT NULL,
 review_status TEXT NOT NULL DEFAULT 'unreviewed'
);
CREATE INDEX IF NOT EXISTS response_expiry ON responses(expires_at);
CREATE TABLE IF NOT EXISTS contacts (
 response_id TEXT PRIMARY KEY REFERENCES responses(id) ON DELETE CASCADE,
 encrypted_email TEXT NOT NULL, expires_at INTEGER NOT NULL,
 privacy_version TEXT NOT NULL, consent_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS contact_expiry ON contacts(expires_at);
CREATE TABLE IF NOT EXISTS rate_limits (
 bucket TEXT PRIMARY KEY, attempts INTEGER NOT NULL, expires_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS rate_expiry ON rate_limits(expires_at);
