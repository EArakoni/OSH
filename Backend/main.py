from fastapi import FastAPI, Query
import sqlite3
import os
import feedparser
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI(title="Lore Kernel Summarizer API")

DB_PATH = "lore_messages.db"

def get_db():
    return sqlite3.connect(DB_PATH)


@app.get("/")
def home():
    return {"message": "Welcome to the Lore Summarizer API 🚀"}

@app.get("/messages")
def get_messages(limit: int = 10):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT subject, author, date, url, summary
        FROM messages
        ORDER BY date DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return [
        {"subject": r[0], "author": r[1], "date": r[2], "url": r[3], "summary": r[4]}
        for r in rows
    ]

@app.get("/search")
def search_messages(q: str = Query(..., description="Keyword to search in subject")):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT subject, author, date, url, summary
        FROM messages
        WHERE subject LIKE ?
        ORDER BY date DESC
    """, (f"%{q}%",))
    rows = cur.fetchall()
    conn.close()
    return [
        {"subject": r[0], "author": r[1], "date": r[2], "url": r[3], "summary": r[4]}
        for r in rows
    ]

@app.post("/refresh")
def refresh_data():
    """Fetch new entries from Lore and summarize them."""
    feed = feedparser.parse("https://lore.kernel.org/lkml/?format=atom")
    conn = get_db()
    cur = conn.cursor()
    model = genai.GenerativeModel("gemini-1.5-flash")

    added = 0
    for entry in feed.entries:
        # Avoid duplicates
        cur.execute("SELECT id FROM messages WHERE url = ?", (entry.link,))
        if cur.fetchone():
            continue

        subject = entry.title
        author = entry.get("author", "")
        date = entry.get("published", "")
        url = entry.link
        content = entry.get("summary", "")

        prompt = f"Summarize this Linux kernel mailing list message:\n\n{content}"
        try:
            response = model.generate_content(prompt)
            summary = response.text
        except Exception as e:
            summary = f"Error summarizing: {e}"

        cur.execute("""
            INSERT INTO messages (subject, author, date, url, content, summary)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (subject, author, date, url, content, summary))
        added += 1

    conn.commit()
    conn.close()
    return {"added": added, "message": "Database updated successfully ✅"}
