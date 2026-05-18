# LegacyDocs

**Auto-generate documentation from code. No docstrings required.**

LegacyDocs scans your codebase, extracts structure and patterns, and generates comprehensive markdown documentation. Works even on undocumented code — understands code intent from patterns.

## Features

- **No docstrings required** — generates docs from code structure and patterns
- **Multi-language** — Python, JavaScript, TypeScript, Go, Rust, PHP
- **Coverage tracking** — shows % of code documented
- **Hierarchical output** — organized by module/package
- **Pattern recognition** — identifies business logic, API endpoints, utilities
- **Self-hosted** — runs locally, no external service

## Quick Start

```bash
# Generate docs for project
python legacy_docs.py --path /path/to/project

# Output to specific directory
python legacy_docs.py --path /path/to/project --output ./docs

# With coverage report
python legacy_docs.py --path /path/to/project --coverage

# Watch mode (auto-regenerate on changes)
python legacy_docs.py --path /path/to/project --watch
```

## Output Structure

```
docs/
├── README.md              # Project overview
├── MODULES.md             # Module structure
├── COVERAGE.md            # Documentation coverage
├── api/
│   ├── endpoints.md       # API endpoints
│   └── schemas.md         # Data schemas
├── services/
│   └── business-logic.md  # Business logic
└── utils/
    └── utilities.md       # Helper functions
```

## Documentation Coverage

LegacyDocs tracks documentation quality:

| Coverage | Rating | Action |
|----------|--------|--------|
| 80%+ | Excellent | Maintain |
| 60-80% | Good | Improve gradually |
| 40-60% | Fair | Prioritize gaps |
| <40% | Poor | Needs work |

## Hermes Integration

```bash
# Via skill
/hermes legacy-docs --path ~/projects/myapp

# Via cron (weekly regeneration)
hermes cron create "0 9 * * 1" --prompt "Run LegacyDocs on ~/projects and commit changes"
```

## Documentation

See [docs/](docs/) for full documentation.