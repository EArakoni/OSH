# 🤝 Contributing to LKML Dashboard

Thank you for your interest in contributing to LKML Dashboard! This project aims to democratize Linux Kernel development by making LKML accessible to everyone.

We welcome contributions from developers of all skill levels. Whether you're fixing a typo, adding a feature, or improving documentation, your help is appreciated!

---

## 📋 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [How Can I Contribute?](#how-can-i-contribute)
3. [Getting Started](#getting-started)
4. [Development Workflow](#development-workflow)
5. [Style Guidelines](#style-guidelines)
6. [Commit Guidelines](#commit-guidelines)
7. [Pull Request Process](#pull-request-process)

---

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

**TL;DR:** Be respectful, inclusive, and professional. We're all here to make kernel development more accessible.

---

## How Can I Contribute?

### 🐛 Reporting Bugs

Before creating a bug report:
- **Check existing issues** - Your bug might already be reported
- **Try the latest version** - It might already be fixed
- **Check documentation** - Make sure it's actually a bug

**How to submit a good bug report:**

1. **Use a clear, descriptive title**
   - ❌ "It doesn't work"
   - ✅ "API returns 500 error when searching for emails with special characters"

2. **Provide detailed steps to reproduce**
   ```markdown
   Steps to reproduce:
   1. Start the API: `python api.py`
   2. Open browser to http://localhost:5000/api/search?q=<test>
   3. Observe 500 error
   ```

3. **Include system information**
   - OS (Ubuntu 22.04, macOS 13, Windows 11, etc.)
   - Python version (`python --version`)
   - Node version (`node --version`)

4. **Attach logs or screenshots** if applicable

**Use this template:**
```markdown
**Bug Description:**
Brief description of the issue

**Steps to Reproduce:**
1. Step one
2. Step two
3. See error

**Expected Behavior:**
What should happen

**Actual Behavior:**
What actually happens

**Environment:**
- OS: Ubuntu 22.04
- Python: 3.10.12
- Browser: Chrome 120

**Additional Context:**
Any other relevant information
```

---

### ✨ Suggesting Features

We love new ideas! Before suggesting a feature:
- **Check existing issues** - It might already be proposed
- **Consider the scope** - Does it align with project goals?
- **Think about implementation** - How would it work?

**How to submit a good feature request:**

1. **Use a clear, descriptive title**
   - ❌ "Add more features"
   - ✅ "Add weekly digest email notifications"

2. **Explain the problem you're solving**
   ```markdown
   Currently, users must manually check the dashboard daily.
   A weekly digest would allow them to stay updated via email.
   ```

3. **Describe your proposed solution**
   ```markdown
   Add a scheduled job that:
   1. Generates weekly summary using existing Gemini summarization
   2. Sends email via SendGrid/Mailgun
   3. Allows users to configure frequency in settings
   ```

4. **Consider alternatives**
   ```markdown
   Alternative: RSS feed instead of email
   Alternative: Slack/Discord webhooks
   ```

---

### 📝 Improving Documentation

Documentation improvements are highly valued! You can:
- Fix typos or grammatical errors
- Add missing sections
- Improve existing explanations
- Add code examples
- Create tutorials

**No pull request is too small** - even fixing a single typo helps!

---

### 💻 Contributing Code

**Good first issues:**
- Documentation improvements
- Adding tests
- Fixing bugs labeled `good-first-issue`
- Adding error handling
- Improving logging

**Intermediate issues:**
- Adding new API endpoints
- Improving search relevance
- Adding email sources (Patchwork, etc.)
- Frontend components

**Advanced issues:**
- Performance optimization
- Database migration to PostgreSQL
- Real-time webhook integration
- Mobile app development

---

## Getting Started

### Prerequisites

1. **Fork the repository** on GitHub
2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR-USERNAME/lkml-dashboard.git
   cd lkml-dashboard
   ```

3. **Add upstream remote**
   ```bash
   git remote add upstream https://github.com/ORIGINAL-OWNER/lkml-dashboard.git
   ```

4. **Set up development environment**
   - Follow [SETUP.md](docs/SETUP.md)
   - Make sure all tests pass

---

## Development Workflow

### 1. Create a Branch

```bash
# Update your local main
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
# Or for bugs:
git checkout -b fix/bug-description
```

**Branch naming:**
- `feature/add-weekly-digest` - New features
- `fix/search-special-chars` - Bug fixes
- `docs/improve-api-guide` - Documentation
- `refactor/cleanup-parser` - Code refactoring
- `test/add-api-tests` - Adding tests

### 2. Make Changes

**Write clean, readable code:**
- Follow existing code style
- Add comments for complex logic
- Write self-documenting code

**Backend (Python):**
```python
def process_thread(thread_id: int) -> Optional[Dict]:
    """
    Process and summarize a thread.
    
    Args:
        thread_id: Database ID of the thread
        
    Returns:
        Summary dictionary or None if error
    """
    # Implementation here
```

**Frontend (React/TypeScript):**
```typescript
interface ThreadProps {
  threadId: number;
  onClose: () => void;
}

/**
 * Displays thread details with AI summary
 */
const ThreadDetail: React.FC<ThreadProps> = ({ threadId, onClose }) => {
  // Implementation here
};
```

### 3. Test Your Changes

**Backend tests:**
```bash
cd Backend

# Test specific functionality
python main.py stats
python main.py search "test"

# Test API
python api.py &
curl http://localhost:5000/api/stats

# Run test suite (when available)
pytest
```

**Frontend tests:**
```bash
cd Frontend

# Run tests
npm test

# Run linter
npm run lint

# Build to check for errors
npm run build
```

### 4. Commit Your Changes

Follow our [commit guidelines](#commit-guidelines):

```bash
git add .
git commit -m "feat: add weekly digest generation

- Add weekly_digest.py module
- Integrate with Gemini API
- Add CLI command: main.py digest --weekly
- Update documentation

Closes #123"
```

### 5. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 6. Create Pull Request

1. Go to your fork on GitHub
2. Click "New Pull Request"
3. Select your feature branch
4. Fill out the PR template
5. Submit!

---

## Style Guidelines

### Python Code Style

We follow **PEP 8** with some modifications:

```python
# ✅ Good
def parse_email(email_data: Dict[str, Any]) -> Dict:
    """Parse email and extract metadata."""
    message_id = email_data.get('message_id', '')
    subject = email_data.get('subject', '')
    
    return {
        'message_id': message_id,
        'subject': subject
    }

# ❌ Bad
def parse_email(emailData):
    messageId=emailData.get('message_id','')
    return {'message_id':messageId}
```

**Rules:**
- Use type hints
- 4 spaces for indentation (no tabs)
- Maximum line length: 100 characters
- Use docstrings for functions
- Meaningful variable names

### JavaScript/TypeScript Style

We follow **Airbnb Style Guide**:

```typescript
// ✅ Good
const fetchThreads = async (limit: number = 20): Promise<Thread[]> => {
  const response = await fetch(`/api/threads?limit=${limit}`);
  return response.json();
};

// ❌ Bad
function fetchThreads(limit){
  return fetch('/api/threads?limit='+limit).then(r=>r.json())
}
```

**Rules:**
- Use TypeScript types
- Prefer `const` over `let`
- Use arrow functions
- 2 spaces for indentation
- Semicolons required

### Documentation Style

- Use **Markdown** for all documentation
- Add **code examples** where appropriate
- Keep **line length under 80 characters** for readability
- Use **emoji sparingly** and consistently

---

## Commit Guidelines

We follow **Conventional Commits** specification:

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding tests
- `chore`: Maintenance tasks

### Examples

```bash
# Feature
feat(api): add weekly digest endpoint

Add GET /api/digest/weekly endpoint that generates
weekly summary of LKML activity.

Closes #42

# Bug fix
fix(search): handle special characters in query

Escape special characters before passing to FTS5
to prevent SQL injection.

Fixes #38

# Documentation
docs(readme): add installation troubleshooting section

# Refactoring
refactor(parser): simplify email extraction logic

# Multiple changes
feat(gemini): improve caching strategy

- Add cache key versioning
- Implement cache expiration (7 days)
- Add cache statistics endpoint

Closes #55, #56
```

---

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] Tests pass (if applicable)
- [ ] Documentation updated
- [ ] Commit messages follow guidelines
- [ ] Branch is up to date with main

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Refactoring

## Testing
How did you test this?

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Code follows project style
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes
```

### Review Process

1. **Automated checks** must pass (linting, tests)
2. **At least one approval** from maintainer required
3. **Address feedback** - Respond to review comments
4. **Squash commits** if requested
5. **Merge** - Maintainers will merge when ready

### After Merge

- Delete your feature branch
- Pull latest main
- Start next contribution!

---

## Recognition

Contributors will be:
- ✨ Listed in [CONTRIBUTORS.md](CONTRIBUTORS.md)
- 🎉 Mentioned in release notes
- 🏆 Credited in documentation
- 💝 Given our eternal gratitude!

---

## Questions?

- 💬 **GitHub Discussions:** Ask questions, share ideas
- 📧 **Email maintainers:** your.email@example.com
- 📖 **Read docs:** Check docs/ folder

---

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

---

**Thank you for making LKML Dashboard better for everyone! 🚀**
