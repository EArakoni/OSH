# LKML Dashboard - Backend 📧

A Linux Kernel Mailing List (LKML) aggregator and dashboard backend that parses, stores, and will summarize kernel development discussions using LLMs.

## Problem

The Linux Kernel Mailing List receives 500-600+ emails daily. Digest emails are hard to follow. This backend:
- Parses LKML emails from lore.kernel.org archives
- Stores them in a searchable SQLite database
- Organizes emails into conversation threads
- Will use AI to generate summaries (coming soon)
- Provides a CLI for data management

## Features

- ✅ Parse Atom feeds from lore.kernel.org
- ✅ Parse mbox format archives
- ✅ SQLite database with full-text search (FTS5)
- ✅ Automatic thread building from email headers
- ✅ CLI interface for all operations
- 🚧 LLM-powered summaries (Gemini API - coming soon)
- 🚧 REST API (FastAPI - coming soon)

## Quick Start

### 1. Setup
```bash
cd Backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Get Some Data

**Option A: Use an existing Atom feed (fastest for testing)**
```bash
# Download the latest feed
python download_lkml.py --atom

# Process it
python main.py atom lkml-new.atom
```

**Option B: Download a specific day's archive**
```bash
# Download and process in one step
python main.py download 2024-10-15
```

**Option C: Process an existing mbox file**
```bash
python main.py process lkml-2024-10-15.mbox
```

### 3. Explore Your Data
```bash
# Show database statistics
python main.py stats

# View sample emails
python main.py sample -n 5

# Search emails (full-text search)
python main.py search "memory leak"
python main.py search "patch networking"

# Export threads to JSON for analysis
python main.py export threads.json
```

## CLI Commands Reference

### Data Ingestion
```bash
# Process an Atom feed (XML format from lore.kernel.org)
python main.py atom <atom_file>
python main.py atom new.atom

# Download and process a specific day (mbox format)
python main.py download YYYY-MM-DD
python main.py download 2024-10-15

# Process an existing mbox file
python main.py process <mbox_file>
python main.py process lkml-2024-10-15.mbox
```

### Data Exploration
```bash
# Show database statistics
python main.py stats

# Show sample emails
python main.py sample              # Shows 5 emails
python main.py sample -n 10        # Shows 10 emails

# Search emails (uses SQLite FTS5 full-text search)
python main.py search "query"
python main.py search "memory leak"

# Export threads to JSON
python main.py export output.json
python main.py export threads.json
```

### Database Options
```bash
# Use a different database file
python main.py --db custom.db stats
python main.py --db production.db atom new.atom

# Default database is lkml.db
```

## Direct SQLite Access

You can also query the database directly:
```bash
# Open database
sqlite3 lkml.db

# Example queries
.mode column
.headers on

-- See all emails
SELECT id, subject, from_address FROM emails LIMIT 10;

-- See threads with most emails
SELECT subject, email_count FROM threads ORDER BY email_count DESC LIMIT 10;

-- Full-text search
SELECT subject FROM emails WHERE id IN (
    SELECT rowid FROM emails_fts WHERE emails_fts MATCH 'networking'
);

-- Get emails in a specific thread
SELECT e.subject, e.from_address, e.date
FROM emails e
JOIN thread_emails te ON e.id = te.email_id
WHERE te.thread_id = 1
ORDER BY e.date;

.quit
```

## Database Schema

### `emails` table
- **message_id** (TEXT, UNIQUE): Email's unique Message-ID
- **subject** (TEXT): Email subject line
- **from_address** (TEXT): Sender email and name
- **date** (TEXT): ISO 8601 datetime
- **body** (TEXT): Email body content
- **in_reply_to** (TEXT): Message-ID of parent email
- **references_list** (TEXT): JSON array of referenced message IDs
- **raw_email** (TEXT): Original email data (first 1000 chars)

### `threads` table
- **root_message_id** (TEXT, UNIQUE): Message-ID of thread root
- **subject** (TEXT): Thread subject
- **participant_count** (INTEGER): Number of unique senders
- **email_count** (INTEGER): Number of emails in thread
- **first_post** (TEXT): Timestamp of first email
- **last_post** (TEXT): Timestamp of most recent email
- **tags** (TEXT): JSON array of tags from subject line (e.g., ["PATCH", "v2"])

### `thread_emails` table
- Junction table linking emails to threads

### `summaries` table (prepared for LLM integration)
- **thread_id** (INTEGER): Reference to thread
- **summary_type** (TEXT): 'daily', 'thread', or 'weekly'
- **tldr** (TEXT): Short summary
- **key_points** (TEXT): JSON array of key points
- **important_changes** (TEXT): JSON object of notable changes
- **mentioned_subsystems** (TEXT): JSON array of kernel subsystems
- **llm_model** (TEXT): Model used for generation

### `emails_fts` table
- FTS5 virtual table for full-text search on subject and body

## Project Structure
```
Backend/
├── src/
│   ├── parser/
│   │   ├── atom_parser.py      # Parse Atom/RSS feeds
│   │   ├── email_parser.py     # Parse mbox format
│   │   ├── thread_builder.py   # Build thread relationships
│   │   └── pipeline.py         # Processing orchestrator
│   ├── database/
│   │   ├── schema.sql          # SQLite schema
│   │   └── db.py               # Database operations
│   └── llm/                    # LLM integration (TODO)
├── main.py                     # CLI interface
├── download_lkml.py            # Download utility
└── requirements.txt            # Python dependencies
```

## How It Works

### Email Parsing
1. Downloads Atom feeds or mbox archives from lore.kernel.org
2. Extracts email metadata (subject, sender, date, Message-ID)
3. Parses email bodies (handles multipart MIME)
4. Decodes encoded headers (UTF-8, etc.)

### Thread Building
1. Uses `In-Reply-To` and `References` headers
2. Follows chains back to root message
3. Groups all emails by thread
4. Calculates thread metadata (participant count, date range, etc.)
5. Extracts tags from subject lines (e.g., [PATCH v2])

### Storage
1. Stores emails in SQLite with normalized schema
2. Links emails to threads via junction table
3. Creates FTS5 index for full-text search
4. Maintains referential integrity

### Search
- Uses SQLite's FTS5 for fast full-text search
- Searches across both subject and body
- Ranks results by relevance

## Data Sources

### Atom Feeds (Recommended for Testing)
- URL: `https://lore.kernel.org/lkml/new.atom`
- Contains ~25 most recent emails
- Easy to parse, structured XML
- Updated continuously

### Mbox Archives (For Historical Data)
- URL pattern: `https://lore.kernel.org/lkml/YYYY-MM-DD/mbox.gz`
- Contains full day of emails (~500-600 emails)
- Standard Unix mbox format
- Available for past dates

## Development Roadmap

### Completed ✅
- [x] Atom feed parser
- [x] Mbox parser
- [x] SQLite database schema
- [x] Thread builder
- [x] Full-text search (FTS5)
- [x] CLI interface
- [x] Database statistics

### In Progress 🚧
- [ ] Gemini API integration
- [ ] Email summarization
- [ ] Thread summarization
- [ ] Daily digest generation

### Planned 📋
- [ ] FastAPI REST API
- [ ] Automatic data fetching (cron/scheduler)
- [ ] Webhook for real-time updates
- [ ] Email classification (patch, discussion, etc.)
- [ ] Sentiment analysis
- [ ] Contributor analytics

## Troubleshooting

### Database locked error
```bash
# Close all connections to the database
# SQLite only allows one writer at a time
```

### Import errors
```bash
# Make sure you're in the Backend directory
cd Backend

# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Atom feed download fails (403 error)
```bash
# lore.kernel.org sometimes blocks automated requests
# Solution: Download manually in browser, save as new.atom
# Or try again later
```

### No emails inserted
```bash
# Check if the file exists and has content
ls -lh new.atom
head -20 new.atom

# Try processing with verbose output
python main.py atom new.atom --db test.db
```

## Testing
```bash
# Test with a fresh database
rm -f test.db
python main.py --db test.db atom new.atom
python main.py --db test.db stats
python main.py --db test.db sample

# Verify database structure
sqlite3 test.db ".schema emails"
```

## Contributing

This is a hackathon project. Pull requests welcome!

## License

MIT License - See LICENSE file

## Acknowledgments

- Linux Kernel Mailing List community
- lore.kernel.org for public archives
- SQLite FTS5 for excellent full-text search
```
