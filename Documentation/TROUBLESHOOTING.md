# 🔧 Troubleshooting Guide

Common issues and their solutions for LKML Dashboard.

---

## 📑 Table of Contents

1. [Backend Issues](#backend-issues)
2. [Frontend Issues](#frontend-issues)
3. [Gemini API Issues](#gemini-api-issues)
4. [Auth0 Issues](#auth0-issues)
5. [Database Issues](#database-issues)
6. [Performance Issues](#performance-issues)

---

## Backend Issues

### ❌ "ModuleNotFoundError: No module named 'flask'"

**Problem:** Dependencies not installed

**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

---

### ❌ "Address already in use" (Port 5000)

**Problem:** Another process is using port 5000

**Solution 1 - Kill the process:**
```bash
# Linux/Mac
lsof -ti:5000 | xargs kill -9

# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

**Solution 2 - Use different port:**
```python
# In api.py, change last line:
app.run(debug=True, port=5001, host='0.0.0.0')  # Use port 5001
```

Then update frontend `.env`:
```env
REACT_APP_API_URL=http://localhost:5001
```

---

### ❌ "ImportError: cannot import name 'LKMLEmailParser'"

**Problem:** Old code or incorrect import

**Solution:**
```bash
# Pull latest code
git pull

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -name "*.pyc" -delete

# Reinstall
pip install -r requirements.txt
```

---

### ❌ "sqlite3.OperationalError: database is locked"

**Problem:** Multiple processes accessing database

**Solution:**
```bash
# Close all terminals running main.py or api.py
# Then restart

# Or delete lock file
rm lkml.db-journal

# Restart API
python api.py
```

---

### ❌ "No such file or directory: 'lkml.db'"

**Problem:** Database file missing

**Solution:**
```bash
# Check if you're in Backend directory
pwd  # Should end with /Backend

# If database is missing, either:
# 1. Pull from git (pre-populated)
git pull

# 2. Or create fresh database
python main.py atom new.atom  # Process some emails first
```

---

## Frontend Issues

### ❌ "npm ERR! code ENOENT"

**Problem:** npm not finding package.json

**Solution:**
```bash
# Make sure you're in Frontend directory
cd Frontend

# Verify package.json exists
ls -la package.json

# Install
npm install
```

---

### ❌ "Port 3000 is already in use"

**Problem:** Another React app is running

**Solution 1 - Kill the process:**
```bash
# Linux/Mac
lsof -ti:3000 | xargs kill -9

# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

**Solution 2 - Use different port:**
```bash
# Set port in .env
echo "PORT=3001" >> .env

# Or run with custom port
PORT=3001 npm start
```

---

### ❌ "CORS Error: No 'Access-Control-Allow-Origin' header"

**Problem:** Backend CORS not configured or not running

**Solution:**
```bash
# 1. Make sure backend is running
cd Backend
python api.py

# 2. Verify Flask-CORS is installed
pip install flask-cors

# 3. Check api.py has this line:
# CORS(app)

# 4. Restart both backend and frontend
```

---

### ❌ "Failed to fetch" or "Network Error"

**Problem:** Backend not running or wrong URL

**Solution:**
```bash
# 1. Check backend is running
curl http://localhost:5000/api/stats

# 2. If backend is on different port, update frontend .env:
REACT_APP_API_URL=http://localhost:5001

# 3. Restart frontend
npm start
```

---

## Gemini API Issues

### ❌ "API key required. Set GEMINI_API_KEY"

**Problem:** API key not set in environment

**Solution:**
```bash
# Set temporarily (Linux/Mac)
export GEMINI_API_KEY='your-key-here'

# Set temporarily (Windows PowerShell)
$env:GEMINI_API_KEY='your-key-here'

# Set permanently - create Backend/.env:
echo "GEMINI_API_KEY=your-key-here" > .env

# Verify it's set
echo $GEMINI_API_KEY  # Linux/Mac
echo $env:GEMINI_API_KEY  # Windows PowerShell
```

---

### ❌ "404 models/gemini-1.5-flash is not found"

**Problem:** Incorrect model name

**Solution:**
```python
# In gemini_client.py, verify MODELS dict has 'models/' prefix:
MODELS = {
    'flash': 'models/gemini-2.5-flash',     # ✅ Correct
    # NOT 'flash': 'gemini-2.5-flash',     # ❌ Wrong
}
```

---

### ❌ "finish_reason: 2" or "Response blocked"

**Problem:** Output token limit reached or safety filter

**Solution 1 - Increase token limit:**
```python
# In gemini_client.py, update generation_config:
self.generation_config = {
    'max_output_tokens': 8192,  # Increase from 2048
}
```

**Solution 2 - Clear cache if you had old responses:**
```bash
rm -rf cache/gemini/*
```

---

### ❌ "Quota exceeded" or "Rate limit"

**Problem:** Too many API calls too quickly

**Solution:**
```bash
# 1. Wait a few minutes and try again

# 2. Reduce rate limit in gemini_client.py:
self.rate_limit = 10  # Lower from 15

# 3. Use caching (should be enabled by default)
client = GeminiClient(enable_cache=True)

# 4. Check your quota at:
# https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas
```

---

### ❌ "JSON parse error" when summarizing

**Problem:** Gemini returning malformed JSON

**Solution:**
This is already handled in the improved code, but verify:
```python
# In gemini_client.py, _parse_json_response should handle markdown:
if cleaned.startswith('```'):
    start = cleaned.find('{')
    end = cleaned.rfind('}')
    cleaned = cleaned[start:end+1]
```

If still getting errors:
```bash
# Clear cache
rm -rf cache/gemini/*

# Try with a different thread
python main.py summarize --limit 1
```

---

## Auth0 Issues

### ❌ "Invalid state" when logging in

**Problem:** Auth0 configuration mismatch

**Solution:**
```bash
# 1. Check .env has correct values
cat Frontend/.env

# 2. Verify in Auth0 dashboard:
# - Allowed Callback URLs: http://localhost:3000/callback
# - Allowed Logout URLs: http://localhost:3000
# - Allowed Web Origins: http://localhost:3000

# 3. Make sure you're using the right domain and client ID

# 4. Clear browser cache and try again
```

---

### ❌ "Missing required parameter: redirect_uri"

**Problem:** Auth0 callback URL not configured

**Solution:**
```javascript
// In Frontend/src/index.js, verify Auth0Provider has:
<Auth0Provider
  domain={process.env.REACT_APP_AUTH0_DOMAIN}
  clientId={process.env.REACT_APP_AUTH0_CLIENT_ID}
  redirectUri={window.location.origin}  // ← Make sure this is set
>
```

---

### ❌ "Cross-Origin-Opener-Policy policy"

**Problem:** Browser security policy blocking popup

**Solution:**
```javascript
// Use redirect instead of popup
const { loginWithRedirect } = useAuth0();

// Don't use loginWithPopup
```

---

## Database Issues

### ❌ "No such table: emails"

**Problem:** Database not initialized

**Solution:**
```bash
# Delete and reinitialize
rm lkml.db

# Process some emails to create schema
python main.py atom new.atom
```

---

### ❌ "UNIQUE constraint failed: emails.message_id"

**Problem:** Trying to insert duplicate email

**This is normal** - the code handles this gracefully. The email already exists in the database.

---

### ❌ "Database disk image is malformed"

**Problem:** Corrupted database file

**Solution:**
```bash
# Backup current database
cp lkml.db lkml.db.backup

# Try to recover
sqlite3 lkml.db ".dump" | sqlite3 lkml_fixed.db
mv lkml_fixed.db lkml.db

# If that doesn't work, restore from git
git checkout lkml.db
```

---

### ❌ "Search returns no results"

**Problem:** FTS5 index not built

**Solution:**
```bash
# Rebuild FTS5 index
sqlite3 lkml.db "INSERT INTO emails_fts(emails_fts) VALUES('rebuild');"

# Test search
python main.py search "test"
```

---

## Performance Issues

### ❌ "API is slow / times out"

**Problem:** Large queries without pagination

**Solution:**
```bash
# Always use limit parameter
curl "http://localhost:5000/api/threads?limit=20"

# Not this:
curl "http://localhost:5000/api/threads"  # Returns all 82 threads
```

---

### ❌ "Summarization is very slow"

**Problem:** Rate limiting or large threads

**Expected behavior:**
- ~10 threads per minute (rate limit = 15/min but retries)
- 82 threads = ~8-10 minutes

**To speed up:**
```python
# Use faster model
client = GeminiClient(model='flash-8b')  # Faster than 'flash'

# Or increase rate limit (risky)
client.rate_limit = 20  # May hit quota
```

---

### ❌ "Frontend loads slowly"

**Problem:** Fetching too much data at once

**Solution:**
```javascript
// Use pagination
const threads = await fetch(
  'http://localhost:5000/api/threads?limit=20&offset=0'
).then(r => r.json());

// Not this:
const threads = await fetch(
  'http://localhost:5000/api/threads'  // All threads
).then(r => r.json());
```

---

## General Debugging

### Enable Debug Mode

**Backend:**
```python
# In api.py, already set to debug=True
app.run(debug=True, port=5000)
```

**Frontend:**
```javascript
// In browser console
localStorage.debug = '*'
```

### Check Logs

**Backend logs:**
```bash
# Flask shows logs in terminal where api.py is running
# Look for error messages
```

**Frontend logs:**
```bash
# Open browser DevTools (F12)
# Check Console tab for errors
# Check Network tab for failed requests
```

### Test Components Individually

**Test database:**
```bash
python main.py stats
sqlite3 lkml.db "SELECT COUNT(*) FROM emails;"
```

**Test API:**
```bash
curl http://localhost:5000/api/health
curl http://localhost:5000/api/stats
```

**Test Gemini:**
```bash
python test_gemini.py
```

**Test Auth0:**
```bash
# Check environment variables
cat Frontend/.env
```

---

## Still Stuck?

### Before Asking for Help

1. **Check error message carefully** - It usually tells you what's wrong
2. **Google the error** - Someone else probably had the same issue
3. **Read relevant documentation** - Check docs/ folder
4. **Try in a fresh terminal** - Sometimes old environment variables interfere

### Getting Help

When asking for help, include:

1. **What you were trying to do**
   ```
   "I was trying to start the backend API"
   ```

2. **What command you ran**
   ```bash
   python api.py
   ```

3. **Full error message**
   ```
   Traceback (most recent call last):
   ...
   ModuleNotFoundError: No module named 'flask'
   ```

4. **Your environment**
   ```
   OS: Ubuntu 22.04
   Python: 3.10.12
   Node: 18.17.0
   ```

5. **What you've already tried**
   ```
   "I tried pip install flask but still getting the error"
   ```

### Where to Ask

- 🐛 **GitHub Issues:** https://github.com/yourusername/lkml-dashboard/issues
- 💬 **Discussions:** https://github.com/yourusername/lkml-dashboard/discussions
- 📧 **Email:** your.email@example.com

---

## Quick Fixes Checklist

When something breaks, try these in order:

- [ ] **Restart everything** - Stop backend, frontend, restart both
- [ ] **Check you're in the right directory** - `pwd` should show Backend/ or Frontend/
- [ ] **Virtual environment activated** - See `(venv)` in terminal
- [ ] **Pull latest code** - `git pull`
- [ ] **Reinstall dependencies** - `pip install -r requirements.txt` and `npm install`
- [ ] **Clear cache** - `rm -rf cache/`, `rm -rf node_modules/`
- [ ] **Check environment variables** - `echo $GEMINI_API_KEY`, `cat .env`
- [ ] **Read the error message** - Actually read it, don't just panic
- [ ] **Google the error** - Copy exact error into Google
- [ ] **Check documentation** - Look in docs/ folder

---

**🎯 99% of issues are solved by one of the solutions above!**
