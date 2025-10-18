# LKML Dashboard 📧

A Linux Kernel Mailing List (LKML) aggregator and dashboard that uses LLMs to summarize and organize the massive amount of daily kernel development discussions.

## Problem

The Linux Kernel Mailing List receives 500-600+ emails daily. Digest emails are hard to follow. This tool:
- Parses LKML emails from archives
- Organizes them into threads
- Uses AI to generate summaries
- Provides a modern dashboard for kernel developers

## Features

- ✅ Download LKML archives from lore.kernel.org
- ✅ Parse mbox format emails
- ✅ Build thread relationships
- ✅ Full-text search with SQLite FTS5
- ✅ SQLite database (portable, zero-config)
- 🚧 LLM-powered summaries (coming soon)
- 🚧 Modern web dashboard (coming soon)

## Quick Start

### 1. Setup
```bash
# Clone repository
git clone <your-repo>
cd lkml-dashboard

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Download and Process LKML
```bash
# Download and process a specific day
python main.py download 2024-10-17

# Or process an existing mbox file
python main.py process lkml-2024-10-17.mbox
```

### 3. Explore the Data
```bash
# Show statistics
python main.py stats

# Search emails
python main.py search "memory leak"

# Export threads for analysis
python main.py export threads.json
```

### 4. Direct SQLite Access
```bash
# Open database
sqlite3 lkml.db

# Example queries
SELECT COUNT(*) FROM emails;
SELECT subject, from_address FROM emails LIMIT 10;
SELECT * FROM threads ORDER BY email_count DESC LIMIT 5;

# Full-text search
SELECT subject FROM emails WHERE id IN (
    SELECT rowid FROM emails_fts WHERE emails_fts MATCH 'networking'
);
```

## Project Structure
```
lkml-dashboard/
├── src/
│   ├── parser/
│   │   ├── __init__.py
│   │   ├── email_parser.py      # Parse mbox files
│   │   ├── thread_builder.py    # Build thread structure
│   │   └── pipeline.py          # Main processing pipeline
│   ├── database/
│   │   ├── __init__.py
│   │   ├── schema.sql           # Database schema
│   │   └── db.py                # Database operations
│   └── llm/
│       └── __init__.py          # LLM integration (TODO)
├── main.py                      # CLI entry point
├── download_lkml.py             # Download utility
├── test_parser.py               # Test script
├── requirements.txt
└── README.md
```

## Database Schema

### emails
- Core email data (subject, from, body, etc.)
- Threading info (in_reply_to, references)

### threads
- Thread metadata (participant count, date range)
- Root message tracking

### thread_emails
- Links emails to threads

### summaries (TODO)
- LLM-generated summaries
- Key points and TLDR

## How It Works

### Step 1: Email Parsing
1. Download mbox file from lore.kernel.org
2. Parse each email message
3. Extract headers (Message-ID, Subject, From, Date, etc.)
4. Extract body content
5. Handle multipart MIME messages

### Step 2: Thread Building
1. Use In-Reply-To and References headers
2. Follow chain back to root message
3. Group emails by thread
4. Calculate thread metadata

### Step 3: Storage
1. Store emails in SQLite database
2. Link emails to threads
3. Create full-text search index
4. Enable fast queries

### Step 4: LLM Summarization (TODO)
1. Batch emails by day/thread
2. Send to Gemini API
3. Generate structured summaries
4. Store in database

## Development Roadmap

- [x] Email parser
- [x] Thread builder
- [x] SQLite database
- [x] Full-text search
- [x] CLI interface
- [ ] Gemini API integration
- [ ] Daily digest summaries
- [ ] Thread summaries
- [ ] FastAPI backend
- [ ] React dashboard
- [ ] Auth0 authentication
- [ ] Personalized feeds

## Contributing

This is a hackathon project for [Event Name]. Contributions welcome!

## License

MIT License

## Acknowledgments

- Linux Kernel Mailing List
- lore.kernel.org for public archives
- Anthropic Claude for development assistance
