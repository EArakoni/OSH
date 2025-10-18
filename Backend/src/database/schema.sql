-- Emails table: stores individual emails
CREATE TABLE IF NOT EXISTS emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT UNIQUE NOT NULL,
    subject TEXT,
    from_address TEXT,
    date TEXT,  -- SQLite doesn't have native datetime, use TEXT in ISO format
    body TEXT,
    in_reply_to TEXT,
    references_list TEXT,  -- Changed from 'references' (reserved keyword)
    mailing_list TEXT DEFAULT 'linux-kernel',
    raw_email TEXT,  -- Store original for debugging
    created_at TEXT DEFAULT (datetime('now'))
);

-- Threads table: groups related emails
CREATE TABLE IF NOT EXISTS threads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    root_message_id TEXT UNIQUE NOT NULL,
    subject TEXT,
    participant_count INTEGER DEFAULT 0,
    email_count INTEGER DEFAULT 0,
    first_post TEXT,
    last_post TEXT,
    tags TEXT,  -- JSON array as text
    FOREIGN KEY (root_message_id) REFERENCES emails(message_id)
);

-- Thread membership: which emails belong to which threads
CREATE TABLE IF NOT EXISTS thread_emails (
    thread_id INTEGER,
    email_id INTEGER,
    FOREIGN KEY (thread_id) REFERENCES threads(id),
    FOREIGN KEY (email_id) REFERENCES emails(id),
    PRIMARY KEY (thread_id, email_id)
);

-- Summaries table: LLM-generated summaries
CREATE TABLE IF NOT EXISTS summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id INTEGER,
    summary_date TEXT,
    summary_type TEXT,  -- 'daily', 'thread', 'weekly'
    key_points TEXT,  -- JSON array as text
    tldr TEXT,
    important_changes TEXT,  -- JSON as text
    mentioned_subsystems TEXT,  -- JSON array as text
    llm_model TEXT,
    generated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (thread_id) REFERENCES threads(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_emails_date ON emails(date);
CREATE INDEX IF NOT EXISTS idx_emails_message_id ON emails(message_id);
CREATE INDEX IF NOT EXISTS idx_threads_last_post ON threads(last_post);
CREATE INDEX IF NOT EXISTS idx_summaries_date ON summaries(summary_date);

-- Full-text search (FTS5) for email bodies and subjects
CREATE VIRTUAL TABLE IF NOT EXISTS emails_fts USING fts5(
    message_id UNINDEXED,
    subject,
    body,
    content=emails,
    content_rowid=id
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS emails_ai AFTER INSERT ON emails BEGIN
    INSERT INTO emails_fts(rowid, message_id, subject, body)
    VALUES (new.id, new.message_id, new.subject, new.body);
END;

CREATE TRIGGER IF NOT EXISTS emails_ad AFTER DELETE ON emails BEGIN
    DELETE FROM emails_fts WHERE rowid = old.id;
END;

CREATE TRIGGER IF NOT EXISTS emails_au AFTER UPDATE ON emails BEGIN
    UPDATE emails_fts SET subject = new.subject, body = new.body
    WHERE rowid = new.id;
END;
