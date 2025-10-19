# LKML Dashboard API - Frontend Integration Guide

## 🚀 Quick Start

**Base URL:** `http://localhost:5000`

**Start the API:**
```bash
cd Backend
python api.py
```

**Test it works:**
```bash
curl http://localhost:5000/api/stats
```

---

## 📊 Core Endpoints

### 1. Dashboard Statistics

**Endpoint:** `GET /api/stats`

**Use case:** Homepage stats, dashboard metrics

**Response:**
```json
{
  "total_emails": 101,
  "total_threads": 82,
  "summarized_threads": 82,
  "unique_senders": 29,
  "emails_today": 0,
  "coverage_percent": 100.0
}
```

**Frontend example:**
```javascript
const stats = await fetch('http://localhost:5000/api/stats')
  .then(r => r.json());

console.log(`${stats.total_threads} threads, ${stats.coverage_percent}% summarized`);
```

**React example:**
```jsx
function DashboardStats() {
  const [stats, setStats] = useState(null);
  
  useEffect(() => {
    fetch('http://localhost:5000/api/stats')
      .then(r => r.json())
      .then(setStats);
  }, []);
  
  if (!stats) return <div>Loading...</div>;
  
  return (
    <div className="stats">
      <div className="stat-card">
        <h3>{stats.total_threads}</h3>
        <p>Total Threads</p>
      </div>
      <div className="stat-card">
        <h3>{stats.coverage_percent}%</h3>
        <p>AI Summarized</p>
      </div>
      <div className="stat-card">
        <h3>{stats.unique_senders}</h3>
        <p>Contributors</p>
      </div>
    </div>
  );
}
```

---

### 2. Thread List

**Endpoint:** `GET /api/threads`

**Query Parameters:**
- `limit` (default: 20) - Number of threads to return
- `offset` (default: 0) - Pagination offset
- `sort` (default: 'recent') - Sort order: `recent`, `active`, `popular`

**Use case:** Main thread list, infinite scroll

**Example request:**
```
GET /api/threads?limit=10&sort=active
```

**Response:**
```json
{
  "threads": [
    {
      "id": 44,
      "subject": "[PATCH] maple_tree: Fix potential NULL pointer dereference",
      "email_count": 2,
      "participant_count": 2,
      "first_post": "2025-10-18T19:47:47Z",
      "last_post": "2025-10-18T19:47:47Z",
      "tags": ["PATCH"],
      "tldr": "A patch fixes potential NULL pointer dereferences...",
      "subsystems": ["memory-management"],
      "llm_model": "gemini-2.5-flash"
    }
  ],
  "limit": 10,
  "offset": 0,
  "sort": "active"
}
```

**Frontend example:**
```javascript
// Get 20 most recent threads
const response = await fetch('http://localhost:5000/api/threads?limit=20&sort=recent')
  .then(r => r.json());

response.threads.forEach(thread => {
  console.log(`${thread.subject} - ${thread.email_count} emails`);
  console.log(`Summary: ${thread.tldr}`);
});
```

**React example with pagination:**
```jsx
function ThreadList() {
  const [threads, setThreads] = useState([]);
  const [page, setPage] = useState(0);
  const LIMIT = 20;
  
  useEffect(() => {
    fetch(`http://localhost:5000/api/threads?limit=${LIMIT}&offset=${page * LIMIT}`)
      .then(r => r.json())
      .then(data => setThreads(data.threads));
  }, [page]);
  
  return (
    <div>
      {threads.map(thread => (
        <div key={thread.id} className="thread-card">
          <h3>{thread.subject}</h3>
          <p className="tldr">{thread.tldr}</p>
          <div className="meta">
            <span>{thread.email_count} emails</span>
            <span>{thread.participant_count} participants</span>
            {thread.subsystems?.map(sub => (
              <span key={sub} className="badge">{sub}</span>
            ))}
          </div>
        </div>
      ))}
      
      <button onClick={() => setPage(p => p - 1)} disabled={page === 0}>
        Previous
      </button>
      <button onClick={() => setPage(p => p + 1)}>
        Next
      </button>
    </div>
  );
}
```

---

### 3. Thread Detail (Most Important!)

**Endpoint:** `GET /api/threads/:id`

**Use case:** Thread detail page with full conversation + AI summary

**Example request:**
```
GET /api/threads/44
```

**Response:**
```json
{
  "id": 44,
  "subject": "[PATCH] maple_tree: Fix potential NULL pointer dereference",
  "email_count": 2,
  "participant_count": 2,
  "first_post": "2025-10-18T19:47:47Z",
  "last_post": "2025-10-18T19:47:47Z",
  "tags": ["PATCH"],
  "summary": {
    "tldr": "A patch fixes potential NULL pointer dereferences...",
    "key_points": [
      "Adds NULL checks for mas_pop_node() return values",
      "Prevents kernel crashes in maple tree operations",
      "Tested with stress tests"
    ],
    "subsystems": ["memory-management"],
    "important_changes": {
      "resolution": "Patch accepted",
      "action_items": ["Review by maintainers", "Merge to next"],
      "discussion_summary": "Brief discussion about edge cases...",
      "thread_type": "patch_review"
    },
    "llm_model": "gemini-2.5-flash",
    "generated_at": "2025-10-19T00:46:30.916934"
  },
  "emails": [
    {
      "id": 52,
      "message_id": "20251018194747.1234567-1-dev@kernel.org",
      "subject": "[PATCH] maple_tree: Fix potential NULL pointer dereference",
      "from_address": "Developer <dev@kernel.org>",
      "date": "2025-10-18T19:47:47Z",
      "body": "This patch fixes...",
      "in_reply_to": null
    },
    {
      "id": 53,
      "message_id": "reply@kernel.org",
      "subject": "Re: [PATCH] maple_tree: Fix potential NULL pointer dereference",
      "from_address": "Reviewer <reviewer@kernel.org>",
      "date": "2025-10-18T20:15:00Z",
      "body": "Looks good to me...",
      "in_reply_to": "20251018194747.1234567-1-dev@kernel.org"
    }
  ]
}
```

**React example:**
```jsx
function ThreadDetail({ threadId }) {
  const [thread, setThread] = useState(null);
  
  useEffect(() => {
    fetch(`http://localhost:5000/api/threads/${threadId}`)
      .then(r => r.json())
      .then(setThread);
  }, [threadId]);
  
  if (!thread) return <div>Loading...</div>;
  
  return (
    <div className="thread-detail">
      <h1>{thread.subject}</h1>
      
      {/* AI Summary Section */}
      {thread.summary && (
        <div className="ai-summary">
          <h2>🤖 AI Summary</h2>
          <p className="tldr">{thread.summary.tldr}</p>
          
          <h3>Key Points:</h3>
          <ul>
            {thread.summary.key_points?.map((point, i) => (
              <li key={i}>{point}</li>
            ))}
          </ul>
          
          <div className="badges">
            {thread.summary.subsystems?.map(sub => (
              <span key={sub} className="badge">{sub}</span>
            ))}
          </div>
        </div>
      )}
      
      {/* Email Thread */}
      <div className="emails">
        <h2>Conversation ({thread.email_count} emails)</h2>
        {thread.emails.map(email => (
          <div key={email.id} className="email">
            <div className="email-header">
              <strong>{email.from_address}</strong>
              <span className="date">{new Date(email.date).toLocaleString()}</span>
            </div>
            <div className="email-subject">{email.subject}</div>
            <pre className="email-body">{email.body}</pre>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

### 4. Search

**Endpoint:** `GET /api/search`

**Query Parameters:**
- `q` (required) - Search query
- `limit` (default: 20) - Max results

**Use case:** Search bar, find specific topics

**Example request:**
```
GET /api/search?q=memory+leak&limit=10
```

**Response:**
```json
{
  "query": "memory leak",
  "results": [
    {
      "id": 15,
      "subject": "[PATCH] Fix memory leak in network driver",
      "from_address": "Dev <dev@kernel.org>",
      "date": "2025-10-18T12:00:00Z",
      "snippet": "This patch fixes a <mark>memory leak</mark> in the buffer..."
    }
  ],
  "count": 3
}
```

**Frontend example:**
```javascript
async function searchEmails(query) {
  const response = await fetch(
    `http://localhost:5000/api/search?q=${encodeURIComponent(query)}`
  ).then(r => r.json());
  
  console.log(`Found ${response.count} results for "${response.query}"`);
  return response.results;
}

// Usage
const results = await searchEmails("memory leak");
```

**React search component:**
```jsx
function SearchBar() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setLoading(true);
    const response = await fetch(
      `http://localhost:5000/api/search?q=${encodeURIComponent(query)}`
    ).then(r => r.json());
    
    setResults(response.results);
    setLoading(false);
  };
  
  return (
    <div>
      <form onSubmit={handleSearch}>
        <input 
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Search emails..."
        />
        <button type="submit">Search</button>
      </form>
      
      {loading && <div>Searching...</div>}
      
      <div className="search-results">
        {results.map(result => (
          <div key={result.id} className="result">
            <h4>{result.subject}</h4>
            <p dangerouslySetInnerHTML={{ __html: result.snippet }} />
            <small>{result.from_address} · {result.date}</small>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

### 5. Subsystems

**Endpoint:** `GET /api/subsystems`

**Use case:** Filter by kernel subsystem, show popular areas

**Response:**
```json
[
  { "name": "networking", "count": 15 },
  { "name": "memory-management", "count": 12 },
  { "name": "filesystem", "count": 8 }
]
```

**Frontend example:**
```javascript
const subsystems = await fetch('http://localhost:5000/api/subsystems')
  .then(r => r.json());

// Create filter buttons
subsystems.forEach(sub => {
  console.log(`${sub.name}: ${sub.count} threads`);
});
```

---

### 6. Recent Activity

**Endpoint:** `GET /api/recent`

**Query Parameters:**
- `limit` (default: 10) - Number of items

**Use case:** Activity feed, "what's new"

**Response:**
```json
{
  "emails": [
    {
      "id": 101,
      "subject": "[PATCH] Latest fix",
      "from_address": "dev@kernel.org",
      "date": "2025-10-18T19:47:47Z"
    }
  ],
  "threads": [
    {
      "id": 82,
      "subject": "Discussion thread",
      "last_post": "2025-10-18T19:47:47Z",
      "email_count": 5,
      "tldr": "Summary here..."
    }
  ]
}
```

---

### 7. Top Contributors

**Endpoint:** `GET /api/top-contributors`

**Query Parameters:**
- `limit` (default: 10) - Number of contributors

**Use case:** Leaderboard, contributor stats

**Response:**
```json
[
  {
    "from_address": "Linus Torvalds <torvalds@linux-foundation.org>",
    "email_count": 15
  },
  {
    "from_address": "Greg KH <gregkh@linuxfoundation.org>",
    "email_count": 12
  }
]
```

---

## 🎨 UI Component Examples

### Homepage Dashboard
```jsx
function Dashboard() {
  const [stats, setStats] = useState(null);
  const [recentThreads, setRecentThreads] = useState([]);
  
  useEffect(() => {
    // Load stats
    fetch('http://localhost:5000/api/stats')
      .then(r => r.json())
      .then(setStats);
    
    // Load recent threads
    fetch('http://localhost:5000/api/threads?limit=5&sort=recent')
      .then(r => r.json())
      .then(data => setRecentThreads(data.threads));
  }, []);
  
  return (
    <div className="dashboard">
      <h1>LKML Dashboard</h1>
      
      {stats && (
        <div className="stats-grid">
          <StatCard title="Total Threads" value={stats.total_threads} />
          <StatCard title="AI Coverage" value={`${stats.coverage_percent}%`} />
          <StatCard title="Contributors" value={stats.unique_senders} />
        </div>
      )}
      
      <h2>Recent Threads</h2>
      <ThreadList threads={recentThreads} />
    </div>
  );
}
```

### Thread Card Component
```jsx
function ThreadCard({ thread }) {
  return (
    <div className="thread-card" onClick={() => navigate(`/thread/${thread.id}`)}>
      <h3>{thread.subject}</h3>
      
      {thread.tldr && (
        <p className="tldr">🤖 {thread.tldr}</p>
      )}
      
      <div className="meta">
        <span>📧 {thread.email_count} emails</span>
        <span>👥 {thread.participant_count} participants</span>
        <time>{new Date(thread.last_post).toLocaleDateString()}</time>
      </div>
      
      <div className="tags">
        {thread.tags?.map(tag => (
          <span key={tag} className="tag">{tag}</span>
        ))}
        {thread.subsystems?.map(sub => (
          <span key={sub} className="badge">{sub}</span>
        ))}
      </div>
    </div>
  );
}
```

---

## 🔧 Testing Endpoints

### cURL Examples
```bash
# Get stats
curl http://localhost:5000/api/stats

# Get 5 recent threads
curl http://localhost:5000/api/threads?limit=5

# Get thread detail
curl http://localhost:5000/api/threads/1

# Search
curl "http://localhost:5000/api/search?q=memory%20leak"

# Get subsystems
curl http://localhost:5000/api/subsystems
```

### Browser Testing
Just open these URLs:
- http://localhost:5000/api/stats
- http://localhost:5000/api/threads?limit=5
- http://localhost:5000/api/threads/1
- http://localhost:5000/api/search?q=patch

---

## ⚡ Performance Tips

1. **Pagination:** Always use `limit` and `offset` for large lists
2. **Caching:** Cache stats/subsystems data (updates infrequently)
3. **Debounce search:** Wait 300ms after user stops typing
4. **Loading states:** Show spinners while fetching

---

## 🐛 Troubleshooting

### CORS Error
If you see CORS errors:
1. Make sure `api.py` is running
2. Check Flask-CORS is installed: `pip install flask-cors`
3. API should show: `CORS enabled`

### Empty Response
If endpoints return `[]`:
1. Check database has data: `python main.py stats`
2. Wait for summarization to complete
3. API works with partial data - summaries will appear as they're generated

### Connection Refused
1. Start the API: `python api.py`
2. Check it's running on port 5000
3. Use `http://localhost:5000` (not https)

---

## 📦 Data Models Reference

### Thread Object
```typescript
interface Thread {
  id: number;
  subject: string;
  email_count: number;
  participant_count: number;
  first_post: string;  // ISO datetime
  last_post: string;   // ISO datetime
  tags: string[];      // e.g., ["PATCH", "v2"]
  tldr?: string;       // AI-generated summary
  subsystems?: string[]; // e.g., ["networking", "mm"]
  llm_model?: string;  // "gemini-2.5-flash"
}
```

### Email Object
```typescript
interface Email {
  id: number;
  message_id: string;
  subject: string;
  from_address: string;
  date: string;        // ISO datetime
  body: string;
  in_reply_to: string | null;
}
```

### Summary Object
```typescript
interface Summary {
  tldr: string;
  key_points: string[];
  subsystems: string[];
  important_changes: {
    resolution: string;
    action_items: string[];
    discussion_summary: string;
    thread_type: string;
  };
  llm_model: string;
  generated_at: string;  // ISO datetime
}
```

---

## 🚀 Quick Integration Checklist

- [ ] API running on http://localhost:5000
- [ ] Test `/api/stats` returns data
- [ ] Test `/api/threads` returns threads
- [ ] Test `/api/threads/1` returns thread detail
- [ ] CORS working (no browser errors)
- [ ] Search returns results
- [ ] Display thread list in UI
- [ ] Display thread detail with AI summary
- [ ] Search functionality works

---

**Questions?** The API is self-documenting at http://localhost:5000

**Need more endpoints?** Let me know and I'll add them!
