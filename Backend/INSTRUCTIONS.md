# Upgrade Instructions - Improved Gemini Integration

## What's New

### Major Improvements
1. **✅ Updated model names** - Fixed deprecated preview models
2. **⏱️ Rate limiting** - Prevents API quota errors
3. **🔄 Automatic retry** - Exponential backoff for failed requests
4. **💾 Response caching** - Saves money and speeds up re-runs
5. **📊 Usage metrics** - Track API calls, costs, and cache hits
6. **🎯 Better error handling** - Distinguishes quota, safety, and network errors
7. **🧠 Smarter thread truncation** - Keeps important emails (patches, root, latest)
8. **📈 Batch processing** - Process multiple emails efficiently

## Installation

### 1. Install New Dependencies

```bash
cd Backend
source venv/bin/activate  # Or: venv\Scripts\activate on Windows

# Install tenacity for retry logic
pip install tenacity

# If not already installed:
pip install google-generativeai
```

### 2. Replace Files

Replace these two files with the improved versions:

- `Backend/src/llm/gemini_client.py` → Use artifact "gemini_client.py (Improved)"
- `Backend/src/llm/summarizer.py` → Use artifact "summarizer.py (Improved)"

```bash
# Backup old files first
cp src/llm/gemini_client.py src/llm/gemini_client.py.backup
cp src/llm/summarizer.py src/llm/summarizer.py.backup

# Then copy the new files from the artifacts
```

### 3. Update requirements.txt

Add this line to `Backend/requirements.txt`:

```
tenacity==8.2.3
```

## Testing the Improvements

### Test 1: Basic Functionality
```bash
python test_gemini.py
```

Should show:
- ✅ Model initialization
- ✅ Cache enabled message
- ✅ Rate limit info
- ✅ Test summarization

### Test 2: Cache Testing
```python
from src.llm.gemini_client import GeminiClient

client = GeminiClient(model='flash')

# First call - hits API
test_email = {
    'message_id': 'test@example.com',
    'subject': '[PATCH] Fix bug',
    'body': 'This fixes a critical bug...',
    'from': 'dev@kernel.org'
}

summary1 = client.summarize_email(test_email)
print(f"API calls: {client.metrics['api_calls']}")  # Should be 1

# Second call - uses cache
summary2 = client.summarize_email(test_email)
print(f"Cache hits: {client.metrics['cache_hits']}")  # Should be 1

# Show metrics
client.print_metrics()
```

### Test 3: Real Database Summarization
```bash
# Summarize a few threads
python -c "
from src.database.db import Database
from src.llm.gemini_client import GeminiClient
from src.llm.summarizer import LKMLSummarizer

db = Database('lkml.db')
client = GeminiClient(model='flash')
summarizer = LKMLSummarizer(db, client)

# Summarize 3 threads
stats = summarizer.summarize_all_threads(limit=3, min_emails=2)
print(stats)

# Show metrics
client.print_metrics()
summarizer.print_summary_stats()

db.close()
"
```

## New Features You Can Use

### 1. Choose Different Models

```python
# Fast and cheap (recommended)
client = GeminiClient(model='flash')

# Even faster, cheaper
client = GeminiClient(model='flash-8b')

# Better quality, slower, more expensive
client = GeminiClient(model='pro')

# Experimental 2.0 (if available)
client = GeminiClient(model='flash-exp')
```

### 2. Control Caching

```python
# With cache (default)
client = GeminiClient(enable_cache=True)

# Without cache (always hit API)
client = GeminiClient(enable_cache=False)

# Custom cache directory
client = GeminiClient(cache_dir='my_custom_cache')
```

### 3. View Metrics

```python
# Get metrics dictionary
metrics = client.get_metrics()
print(f"Cache hit rate: {metrics['cache_hit_rate']:.1%}")
print(f"Estimated cost: ${metrics['estimated_cost']:.4f}")

# Pretty print
client.print_metrics()
```

### 4. Batch Processing

```python
from src.llm.summarizer import LKMLSummarizer

# Summarize multiple emails efficiently
stats = summarizer.batch_summarize_emails([1, 2, 3, 4, 5])
print(f"Cached: {stats['cached']} out of {stats['success']}")
```

### 5. Weekly Digests

```python
# Generate weekly digest
digest = summarizer.generate_weekly_digest('2025-10-18')
print(digest['tldr'])
```

## Configuration

### Environment Variables

```bash
# Required
export GEMINI_API_KEY='your-api-key-here'

# Optional - choose model (default: flash)
export GEMINI_MODEL='flash'  # or 'flash-8b', 'pro', 'flash-exp'
```

### Cache Location

Default: `Backend/cache/gemini/`

Cache files are named by MD5 hash of content + model name.

```bash
# Clear cache if needed
rm -rf cache/gemini/*

# Or keep it for faster re-runs and cost savings
```

## Troubleshooting

### "Model not found" Error

The model names were updated. Old code used:
- ❌ `models/gemini-2.5-flash-preview-05-20` (expired)
- ❌ `models/gemini-2.5-pro-preview-03-25` (expired)

New code uses:
- ✅ `gemini-1.5-flash` (stable)
- ✅ `gemini-1.5-pro` (stable)

**Fix:** Make sure you're using the new `gemini_client.py`

### Rate Limit Errors

If you see "quota exceeded":

```python
# Reduce rate limit
client = GeminiClient(model='flash')
client.rate_limit = 10  # 10 requests/minute instead of 15

# Or use free tier model
client = GeminiClient(model='flash-8b')  # Cheaper, faster
```

### Import Error: "No module named 'tenacity'"

```bash
pip install tenacity
```

### Cache Not Working

Check cache directory exists and is writable:

```bash
ls -la cache/gemini/
```

If issues:
```python
client = GeminiClient(enable_cache=False)  # Disable cache temporarily
```

## Migration Notes

### Breaking Changes
None! The new code is backward compatible.

### New Features
- Caching (enabled by default)
- Rate limiting (automatic)
- Retry logic (automatic)
- Metrics tracking (automatic)

### Performance Impact
- **First run:** Slightly slower (rate limiting + retry logic overhead)
- **Subsequent runs:** Much faster (caching)
- **Cost savings:** Significant (cache prevents duplicate API calls)

## Cost Estimation

### Before (Old Code)
```
100 thread summaries = 100 API calls
Estimated cost: ~$0.50 (with Flash model)
```

### After (New Code)
```
100 thread summaries:
- First run: 100 API calls ($0.50)
- Second run: 0 API calls ($0.00) ← Cached!
- Editing/testing: 0 API calls ($0.00) ← Cached!
```

**Cache hit rate:** Typically 80-90% after initial run

## Monitoring

### Real-time Metrics

```python
# During processing
client.print_metrics()
```

Output:
```
============================================================
📊 Gemini API Usage Metrics
============================================================
  API calls: 25
  Cache hits: 75
  Cache hit rate: 75.0%
  Errors: 0
  Estimated tokens: 150,000
  Estimated cost: $0.0225
============================================================
```

### Summary Coverage

```python
summarizer.print_summary_stats()
```

Output:
```
============================================================
📊 Summarization Statistics
============================================================
  Total threads: 82
  Summarized threads: 25
  Coverage: 30.5%
  Thread summaries: 25
  Daily digests: 2
  Email summaries: 0
============================================================
```

## Best Practices

1. **Always use cache in production** (saves money)
2. **Start with 'flash' model** (good quality, cheap)
3. **Monitor metrics** to track costs
4. **Use batch processing** for multiple emails
5. **Clear cache** only when model changes or you want fresh summaries

## Support

If you encounter issues:

1. Check the error message carefully
2. Review metrics: `client.print_metrics()`
3. Try disabling cache temporarily: `enable_cache=False`
4. Check API key is valid: `echo $GEMINI_API_KEY`
5. Verify model availability: `GeminiClient.list_available_models()`

## Next Steps

After upgrading:

1. ✅ Test with small dataset (3-5 threads)
2. ✅ Monitor costs with `client.print_metrics()`
3. ✅ Run full summarization when comfortable
4. ✅ Set up daily digest automation (cron job)
5. ✅ Integrate with frontend API
