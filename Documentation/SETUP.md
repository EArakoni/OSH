# 🚀 LKML Dashboard - Complete Setup Guide

This guide will walk you through setting up the LKML Dashboard from scratch.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Backend Setup](#backend-setup)
3. [Frontend Setup](#frontend-setup)
4. [Environment Configuration](#environment-configuration)
5. [Database Population](#database-population)
6. [Verification](#verification)
7. [Next Steps](#next-steps)

---

## Prerequisites

### Required Software

| Software | Version | Download |
|----------|---------|----------|
| **Python** | 3.8+ | https://python.org/downloads |
| **Node.js** | 16+ | https://nodejs.org |
| **npm** | 8+ | (included with Node.js) |
| **Git** | Latest | https://git-scm.com |

### Required API Keys

1. **Google Gemini API Key** (Free)
   - Visit: https://ai.google.dev/
   - Click "Get API Key"
   - Create a new project
   - Copy your API key

2. **Auth0 Account** (Free tier)
   - Visit: https://auth0.com/signup
   - Create application
   - Note: Domain, Client ID, Client Secret

### System Requirements

- **RAM:** 2GB minimum (4GB recommended)
- **Disk Space:** 500MB for code + database
- **OS:** Linux, macOS, or Windows 10+

---

## Backend Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/lkml-dashboard.git
cd lkml-dashboard
```

### Step 2: Navigate to Backend

```bash
cd Backend
```

### Step 3: Create Virtual Environment

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed flask-3.0.0 flask-cors-4.0.0 google-generativeai-0.3.2 tenacity-8.2.3 ...
```

**If you get errors:**
```bash
# Upgrade pip first
pip install --upgrade pip

# Try again
pip install -r requirements.txt
```

### Step 5: Verify Installation

```bash
python -c "import flask; import google.generativeai; print('✅ All dependencies installed')"
```

### Step 6: Set Environment Variables

**Linux/macOS:**
```bash
export GEMINI_API_KEY='your-api-key-here'
```

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY='your-api-key-here'
```

**Windows (CMD):**
```cmd
set GEMINI_API_KEY=your-api-key-here
```

**Permanent setup (recommended):**

Create `.env` file in `Backend/`:
```bash
GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL=flash
```

### Step 7: Test Backend

```bash
# Check database (pre-populated)
python main.py stats

# Expected output:
# ============================================================
# 📊 Database Statistics
# ============================================================
#   Total Emails: 101
#   Total Threads: 82
#   Unique Senders: 29
# ============================================================
```

### Step 8: Start API Server

```bash
python api.py
```

**Expected output:**
```
🚀 Starting LKML Dashboard API
📍 API running at: http://localhost:5000
📖 Documentation: http://localhost:5000

Example requests:
  curl http://localhost:5000/api/stats
  curl http://localhost:5000/api/threads?limit=5

Press Ctrl+C to stop
```

**Test the API:**
```bash
# Open new terminal
curl http://localhost:5000/api/stats
```

✅ **Backend setup complete!**

---

## Frontend Setup

### Step 1: Navigate to Frontend

```bash
cd ../Frontend
```

### Step 2: Install Dependencies

```bash
npm install
```

**Expected output:**
```
added 1234 packages in 30s
```

**If you get errors:**
```bash
# Clear cache and try again
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### Step 3: Configure Auth0

Create `.env` file in `Frontend/`:

```env
REACT_APP_AUTH0_DOMAIN=your-domain.auth0.com
REACT_APP_AUTH0_CLIENT_ID=your-client-id
REACT_APP_API_URL=http://localhost:5000
```

**Get Auth0 credentials:**
1. Go to https://manage.auth0.com
2. Applications → Your App
3. Copy Domain and Client ID

See [AUTH0_SETUP.md](AUTH0_SETUP.md) for detailed instructions.

### Step 4: Start Development Server

```bash
npm start
```

**Expected output:**
```
Compiled successfully!

You can now view lkml-dashboard in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.1.x:3000
```

✅ **Frontend setup complete!**

---

## Environment Configuration

### Backend Environment Variables

Create `Backend/.env`:

```env
# Required
GEMINI_API_KEY=your-api-key-here

# Optional
GEMINI_MODEL=flash                    # Options: flash, flash-8b, pro
DATABASE_PATH=lkml.db                 # Default database location
CACHE_ENABLED=true                    # Enable response caching
CACHE_DIR=cache/gemini                # Cache directory
RATE_LIMIT=15                         # Requests per minute
PORT=5000                             # API port
```

### Frontend Environment Variables

Create `Frontend/.env`:

```env
# Auth0 Configuration
REACT_APP_AUTH0_DOMAIN=your-domain.auth0.com
REACT_APP_AUTH0_CLIENT_ID=your-client-id
REACT_APP_AUTH0_AUDIENCE=https://your-api-audience

# API Configuration
REACT_APP_API_URL=http://localhost:5000

# Optional
REACT_APP_ENV=development
REACT_APP_ENABLE_ANALYTICS=false
```

---

## Database Population

The repository includes a **pre-populated database** with 101 emails and 82 threads.

### Option 1: Use Existing Database (Recommended)

The database is already included! Just verify:

```bash
cd Backend
python main.py stats
```

### Option 2: Populate Fresh Database

If you want to start fresh or add more data:

```bash
# Delete existing database
rm lkml.db

# Download and process latest LKML digest
python download_lkml.py --atom
python main.py atom new.atom

# Or process a specific day
python main.py download 2025-10-18

# Or process EML digest files
python main.py eml path/to/digest.eml
```

### Option 3: Summarize Threads

Generate AI summaries for all threads:

```bash
# Summarize all threads (costs ~$0.05)
python main.py summarize --min-emails 1

# Summarize just 10 threads
python main.py summarize --limit 10

# Check progress
python main.py list-summaries
```

**Estimated time:** ~10 minutes for 82 threads

---

## Verification

### Backend Verification

```bash
cd Backend

# 1. Check database
python main.py stats
# Should show: 101 emails, 82 threads

# 2. Test search
python main.py search "memory"
# Should return matching emails

# 3. Check API
curl http://localhost:5000/api/stats
# Should return JSON with statistics

# 4. Test Gemini (if API key set)
python test_gemini.py
# Should show successful test
```

### Frontend Verification

1. Visit http://localhost:3000
2. You should see the dashboard
3. Click "Login" → Auth0 login screen should appear
4. After login, you should see:
   - Dashboard statistics
   - Thread list
   - Search bar working
   - Thread details clickable

### Full Stack Verification

**Test the complete flow:**

1. **Backend running:** `python api.py` (Port 5000)
2. **Frontend running:** `npm start` (Port 3000)
3. **Open browser:** http://localhost:3000
4. **Login:** Use Auth0 to authenticate
5. **Browse threads:** Click on a thread
6. **View AI summary:** Should see TL;DR and key points
7. **Search:** Type "patch" in search bar
8. **Results:** Should see matching threads

✅ **All systems operational!**

---

## Next Steps

### For Development

1. **Read the documentation:**
   - [API Documentation](API_DOCS.md)
   - [Architecture Overview](ARCHITECTURE.md)
   - [Contributing Guidelines](../CONTRIBUTING.md)

2. **Explore the codebase:**
   ```bash
   # Backend structure
   Backend/
   ├── api.py              # REST API
   ├── main.py             # CLI interface
   ├── src/
   │   ├── llm/            # Gemini integration
   │   ├── parser/         # Email parsers
   │   └── database/       # Database layer
   
   # Frontend structure
   Frontend/
   ├── src/
   │   ├── components/     # React components
   │   ├── pages/          # Page components
   │   ├── services/       # API clients
   │   └── auth/           # Auth0 integration
   ```

3. **Try modifying the code:**
   - Add a new API endpoint
   - Create a new React component
   - Modify the AI prompt for better summaries

### For Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment guide.

### For Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for:
- Code style guidelines
- Pull request process
- Development workflow
- Testing requirements

---

## Common Issues

If you encounter problems, check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) or:

1. **Dependencies fail to install:**
   - Upgrade pip: `pip install --upgrade pip`
   - Use Python 3.8+: `python --version`
   - Check internet connection

2. **API won't start:**
   - Port 5000 already in use? Change port in `api.py`
   - Check if Python virtual environment is activated

3. **Frontend won't start:**
   - Delete `node_modules`, run `npm install` again
   - Check Node.js version: `node --version` (need 16+)

4. **Gemini API errors:**
   - Check API key is set: `echo $GEMINI_API_KEY`
   - Verify key at https://makersuite.google.com/app/apikey
   - Check quota at https://console.cloud.google.com/

5. **Auth0 errors:**
   - Verify credentials in `.env`
   - Check callback URLs in Auth0 dashboard
   - See [AUTH0_SETUP.md](AUTH0_SETUP.md)

---

## Getting Help

- 📖 **Documentation:** Check [docs/](../docs/) folder
- 🐛 **Issues:** https://github.com/yourusername/lkml-dashboard/issues
- 💬 **Discussions:** https://github.com/yourusername/lkml-dashboard/discussions

---

**🎉 Setup complete! Happy hacking!**
