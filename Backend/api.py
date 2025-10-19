#!/usr/bin/env python3
"""
LKML Dashboard - REST API
Simple Flask API for frontend to query the database
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

def get_db():
    """Get database connection"""
    conn = sqlite3.connect('lkml.db')
    conn.row_factory = sqlite3.Row
    return conn

def parse_json_field(value):
    """Parse JSON field, return empty list if None"""
    if value:
        try:
            return json.loads(value)
        except:
            return []
    return []

# ============================================================================
# CORE ENDPOINTS
# ============================================================================

@app.route('/api/stats')
def stats():
    """Get database statistics"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT COUNT(*) as total FROM emails")
    total_emails = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM threads")
    total_threads = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM summaries WHERE summary_type='thread'")
    summarized = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(DISTINCT from_address) as total FROM emails")
    unique_senders = cursor.fetchone()['total']
    
    # Recent activity
    cursor.execute("""
        SELECT COUNT(*) as today 
        FROM emails 
        WHERE date >= date('now', 'start of day')
    """)
    emails_today = cursor.fetchone()['today']
    
    db.close()
    
    return jsonify({
        'total_emails': total_emails,
        'total_threads': total_threads,
        'summarized_threads': summarized,
        'unique_senders': unique_senders,
        'emails_today': emails_today,
        'coverage_percent': round((summarized / total_threads * 100), 1) if total_threads > 0 else 0
    })

@app.route('/api/threads')
def threads():
    """Get list of threads with optional filtering"""
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    sort = request.args.get('sort', 'recent')  # recent, active, popular
    
    db = get_db()
    cursor = db.cursor()
    
    # Build query based on sort
    order_by = {
        'recent': 't.last_post DESC',
        'active': 't.email_count DESC',
        'popular': 't.participant_count DESC'
    }.get(sort, 't.last_post DESC')
    
    cursor.execute(f"""
        SELECT 
            t.id,
            t.subject,
            t.email_count,
            t.participant_count,
            t.first_post,
            t.last_post,
            t.tags,
            s.tldr,
            s.mentioned_subsystems,
            s.llm_model
        FROM threads t
        LEFT JOIN summaries s ON t.id = s.thread_id AND s.summary_type = 'thread'
        ORDER BY {order_by}
        LIMIT ? OFFSET ?
    """, (limit, offset))
    
    threads = []
    for row in cursor.fetchall():
        thread = dict(row)
        thread['tags'] = parse_json_field(thread['tags'])
        thread['subsystems'] = parse_json_field(thread['mentioned_subsystems'])
        del thread['mentioned_subsystems']
        threads.append(thread)
    
    db.close()
    
    return jsonify({
        'threads': threads,
        'limit': limit,
        'offset': offset,
        'sort': sort
    })

@app.route('/api/threads/<int:thread_id>')
def thread_detail(thread_id):
    """Get detailed information about a specific thread"""
    db = get_db()
    cursor = db.cursor()
    
    # Get thread info
    cursor.execute("""
        SELECT * FROM threads WHERE id = ?
    """, (thread_id,))
    
    thread_row = cursor.fetchone()
    if not thread_row:
        db.close()
        return jsonify({'error': 'Thread not found'}), 404
    
    thread = dict(thread_row)
    thread['tags'] = parse_json_field(thread['tags'])
    
    # Get summary
    cursor.execute("""
        SELECT 
            tldr,
            key_points,
            important_changes,
            mentioned_subsystems,
            llm_model,
            generated_at
        FROM summaries 
        WHERE thread_id = ? AND summary_type = 'thread'
        ORDER BY generated_at DESC
        LIMIT 1
    """, (thread_id,))
    
    summary_row = cursor.fetchone()
    if summary_row:
        summary = dict(summary_row)
        summary['key_points'] = parse_json_field(summary['key_points'])
        summary['subsystems'] = parse_json_field(summary['mentioned_subsystems'])
        
        # Parse important_changes JSON
        if summary.get('important_changes'):
            try:
                summary['important_changes'] = json.loads(summary['important_changes'])
            except:
                summary['important_changes'] = {}
        
        del summary['mentioned_subsystems']
        thread['summary'] = summary
    else:
        thread['summary'] = None
    
    # Get emails in thread
    cursor.execute("""
        SELECT 
            e.id,
            e.message_id,
            e.subject,
            e.from_address,
            e.date,
            e.body,
            e.in_reply_to
        FROM emails e
        JOIN thread_emails te ON e.id = te.email_id
        WHERE te.thread_id = ?
        ORDER BY e.date ASC
    """, (thread_id,))
    
    thread['emails'] = [dict(row) for row in cursor.fetchall()]
    
    db.close()
    return jsonify(thread)

@app.route('/api/emails/<int:email_id>')
def email_detail(email_id):
    """Get a specific email"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM emails WHERE id = ?", (email_id,))
    email_row = cursor.fetchone()
    
    if not email_row:
        db.close()
        return jsonify({'error': 'Email not found'}), 404
    
    email = dict(email_row)
    email['references'] = parse_json_field(email['references_list'])
    del email['references_list']
    
    db.close()
    return jsonify(email)

@app.route('/api/search')
def search():
    """Full-text search across emails"""
    query = request.args.get('q', '')
    limit = request.args.get('limit', 20, type=int)
    
    if not query:
        return jsonify({'error': 'Query parameter "q" required'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT 
            e.id,
            e.subject,
            e.from_address,
            e.date,
            snippet(emails_fts, 2, '<mark>', '</mark>', '...', 50) as snippet
        FROM emails e
        JOIN emails_fts ON e.id = emails_fts.rowid
        WHERE emails_fts MATCH ?
        ORDER BY rank
        LIMIT ?
    """, (query, limit))
    
    results = [dict(row) for row in cursor.fetchall()]
    db.close()
    
    return jsonify({
        'query': query,
        'results': results,
        'count': len(results)
    })

@app.route('/api/subsystems')
def subsystems():
    """Get list of subsystems with thread counts"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT mentioned_subsystems 
        FROM summaries 
        WHERE summary_type = 'thread' AND mentioned_subsystems IS NOT NULL
    """)
    
    # Aggregate subsystems
    subsystem_counts = {}
    for row in cursor.fetchall():
        subsystems = parse_json_field(row['mentioned_subsystems'])
        for subsystem in subsystems:
            subsystem_counts[subsystem] = subsystem_counts.get(subsystem, 0) + 1
    
    # Sort by count
    sorted_subsystems = [
        {'name': name, 'count': count}
        for name, count in sorted(subsystem_counts.items(), key=lambda x: x[1], reverse=True)
    ]
    
    db.close()
    return jsonify(sorted_subsystems)

@app.route('/api/recent')
def recent_activity():
    """Get recent emails and threads"""
    limit = request.args.get('limit', 10, type=int)
    
    db = get_db()
    cursor = db.cursor()
    
    # Recent emails
    cursor.execute("""
        SELECT id, subject, from_address, date
        FROM emails
        ORDER BY date DESC
        LIMIT ?
    """, (limit,))
    recent_emails = [dict(row) for row in cursor.fetchall()]
    
    # Recent threads (by last activity)
    cursor.execute("""
        SELECT 
            t.id,
            t.subject,
            t.last_post,
            t.email_count,
            s.tldr
        FROM threads t
        LEFT JOIN summaries s ON t.id = s.thread_id AND s.summary_type = 'thread'
        ORDER BY t.last_post DESC
        LIMIT ?
    """, (limit,))
    recent_threads = [dict(row) for row in cursor.fetchall()]
    
    db.close()
    
    return jsonify({
        'emails': recent_emails,
        'threads': recent_threads
    })

@app.route('/api/top-contributors')
def top_contributors():
    """Get most active email senders"""
    limit = request.args.get('limit', 10, type=int)
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT 
            from_address,
            COUNT(*) as email_count
        FROM emails
        GROUP BY from_address
        ORDER BY email_count DESC
        LIMIT ?
    """, (limit,))
    
    contributors = [dict(row) for row in cursor.fetchall()]
    db.close()
    
    return jsonify(contributors)

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/')
def index():
    """API documentation"""
    return jsonify({
        'name': 'LKML Dashboard API',
        'version': '1.0',
        'endpoints': {
            'GET /api/health': 'Health check',
            'GET /api/stats': 'Database statistics',
            'GET /api/threads?limit=20&offset=0&sort=recent': 'List threads',
            'GET /api/threads/<id>': 'Thread details with emails and summary',
            'GET /api/emails/<id>': 'Single email details',
            'GET /api/search?q=query&limit=20': 'Full-text search',
            'GET /api/subsystems': 'List kernel subsystems',
            'GET /api/recent?limit=10': 'Recent activity',
            'GET /api/top-contributors?limit=10': 'Most active contributors'
        }
    })

if __name__ == '__main__':
    print("🚀 Starting LKML Dashboard API")
    print("📍 API running at: http://localhost:5000")
    print("📖 Documentation: http://localhost:5000")
    print("\nExample requests:")
    print("  curl http://localhost:5000/api/stats")
    print("  curl http://localhost:5000/api/threads?limit=5")
    print("  curl http://localhost:5000/api/search?q=memory")
    print("\nPress Ctrl+C to stop\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')
