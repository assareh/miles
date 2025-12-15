# Claude Assistant Guide - Miles

Developer guide for maintaining the Miles codebase.

## Quick Reference

```bash
# Setup (first time)
./setup.sh                       # Installs uv, Python, and dependencies (includes RAG + WebUI)
# OR
uv sync --extra webui            # Install dependencies manually (includes RAG by default)

# Before every commit
./lint.sh                        # Format and lint

# Manual linting
uv run black .                   # Format code
uv run ruff check --fix .        # Lint with auto-fix

# Run Miles
uv run python miles.py        # With Open Web UI
uv run python miles.py --no-webui  # Without UI
```

## Linting Routine

### Standard Workflow

Always run before committing:

```bash
./lint.sh
```

This script:
1. Formats code with Black (120 char lines)
2. Lints with Ruff (auto-fixes most issues)
3. Verifies all checks pass

### Configuration

All linting settings in `pyproject.toml`:
- **Black**: 120 character lines, Python 3.12
- **Ruff**: Fast linter replacing flake8/pylint/isort
- **Style**: Print statements allowed in main files, os.path preferred over pathlib

### Common Issues

**Unused imports** - Ruff removes automatically
**Quote styles** - Black standardizes to double quotes
**Import sorting** - Ruff organizes: stdlib → third-party → local

## Development Guidelines

### Code Style
- Line length: 120 characters max
- Type hints: `list[dict]` not `List[Dict]`
- Imports: Auto-sorted by Ruff
- Print statements: Allowed in miles.py and tools.py

### Adding Tools

```python
@tool
def new_tool(param: str) -> str:
    """Tool description for LLM."""
    return result
```

Add to `ALL_TOOLS` list in tools.py

### Modifying Data Files

- `credit_cards.json` - Card database (validate JSON)
- `transfer_partners.json` - Transfer relationships
- `system_instruction.md` - System prompt (cached on file change)
- `user.json` - User wallet/preferences (don't commit)

## Git Workflow

```bash
# Make changes
./lint.sh                # Lint code
git add .
git commit -m "feat: description

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"
git push
```

## Repository Structure

```
miles/
├── miles.py              # Main server (uses llm-tools-server)
├── config.py             # Configuration
├── tools.py              # LangChain tools (includes RAG & web search)
├── data_storage.py       # JSON data access
├── test_miles.py         # Comprehensive test suite
├── setup.sh              # Automated setup script
├── apply_branding.sh     # Apply Open Web UI branding
├── lint.sh               # Code formatting and linting
├── data/                 # Reference and user data
├── branding/             # Open Web UI customization
├── doc_index/            # RAG documentation cache (if enabled)
└── pyproject.toml        # Linting config
```

## Key Patterns

### System Prompt Loading
- Cached based on file mtime
- Auto-reloads on file change
- Fallback to default if missing

### Tool Execution
- Debug logging available (DEBUG_TOOLS env var)
- LLM request logging available (DEBUG_LLM_REQUESTS env var)
- JSON logs with timing info
- Error handling with proper exception chaining
- Built-in tools: datetime, calculator, user data, card info, card search, transfer partners, benefits search, web search, doc search (if RAG enabled)

### Backend Support
- LM Studio (OpenAI format)
- Ollama (native format)
- Tool calling loop with max iterations

### RAG Support
- Optional documentation search (disabled by default)
- Hybrid BM25 + semantic search
- Automatic context augmentation
- Configurable via RAG_* environment variables
- Dependencies included by default

## Testing Changes

```bash
# Start server
python miles.py --no-webui --debug

# Test API
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "askmiles/miles", "messages": [{"role": "user", "content": "test"}]}'

# Check health
curl http://localhost:8000/health
```

## IDE Setup

### VS Code

Install extensions:
- Ruff (charliermarsh.ruff)
- Black Formatter (ms-python.black-formatter)

`.vscode/settings.json`:
```json
{
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  },
  "ruff.enable": true
}
```

## Testing

```bash
# Run test suite
uv run python test_miles.py

# Verbose mode (shows full responses)
uv run python test_miles.py --verbose
```

The test suite includes 15 test questions covering all major functionality.

## Resources

- [README.md](README.md) - User documentation
- [TESTING.md](TESTING.md) - Testing documentation
- [Black Docs](https://black.readthedocs.io/)
- [Ruff Docs](https://docs.astral.sh/ruff/)
- [LangChain](https://python.langchain.com/)
- [llm-tools-server](https://github.com/anthropics/llm-tools-server) - Base framework

---

*Last updated: 2025-11-25*
