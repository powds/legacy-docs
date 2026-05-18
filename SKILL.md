---
name: legacy-docs
description: "Auto-generate documentation from code. No docstrings required. Multi-language support, coverage tracking, hierarchical output."
version: 1.0.0
author: powds
license: MIT
metadata:
  legacy-docs:
    tags: [documentation, code-analysis, developer-tools]
    homepage: https://github.com/powds/legacy-docs
---

# LegacyDocs Skill

Auto-generate documentation from code structure. Understands code intent from patterns.

## Usage

### Command Line

```bash
# Generate docs
python legacy_docs.py --path ~/projects/captionhook

# Specific output directory
python legacy_docs.py --path ~/projects/captionhook --output ./generated-docs

# Coverage report only
python legacy_docs.py --path ~/projects/captionhook --coverage

# Watch mode
python legacy_docs.py --path ~/projects/captionhook --watch
```

### Hermes Integration

```bash
# Generate and commit
hermes legacy-docs --path ~/projects/captionhook --commit

# Coverage check
hermes legacy-docs --path ~/projects/captionhook --coverage --report
```

## Output Format

Generates markdown files organized by:

- **Modules** — directory/package structure
- **Files** — per-file documentation
- **Functions** — detected function definitions
- **Classes** — detected class definitions
- **Endpoints** — API routes (if framework detected)
- **Imports** — dependencies

## Coverage Report

```markdown
## Documentation Coverage

| Module | LOC | Functions | Classes | Score |
|--------|-----|-----------|--------|-------|
| app/api | 1,193 | 24 | 8 | 72% |
| app/dashboard | 836 | 12 | 5 | 45% |

Overall: 58% documented (needs improvement)
```

## Configuration

Create `~/.legacy-docs/config.yaml`:

```yaml
output:
  directory: ./docs
  format: markdown
  include_private: false

analysis:
  max_depth: 3
  exclude_patterns:
    - "node_modules"
    - "dist"
    - "*.min.js"

languages:
  python:
    docstring_required: false
    detect_decorators: true
  javascript:
    jsdoc_required: false
    detect_exports: true

coverage:
  weights:
    function: 1.0
    class: 2.0
    file: 0.5
  thresholds:
    excellent: 80
    good: 60
    fair: 40
```

## Files

```
legacy-docs/
├── SKILL.md              # This file
├── legacy_docs.py        # Main script
├── requirements.txt      # Dependencies
├── config.yaml           # Default config
├── docs/
│   ├── ALGORITHM.md      # How doc generation works
│   └── SESSION.md        # Session log
└── README.md             # Project overview
```