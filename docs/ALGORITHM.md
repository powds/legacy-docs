# LegacyDocs Algorithm

This document explains how LegacyDocs generates documentation from code.

## Overview

LegacyDocs uses a three-stage pipeline:
1. **Scan** — Find all supported source files
2. **Parse** — Extract functions, classes, imports from each file
3. **Generate** — Create markdown documentation per module

## Stage 1: Scanning

### File Discovery

```python
for ext_pattern in ['*.py', '*.js', '*.jsx', '*.ts', '*.tsx', '*.go', '*.rs', '*.php']:
    for file_path in Path(root_path).rglob(ext_pattern):
        if not should_exclude(str(file_path)):
            files.append(str(file_path))
```

### Exclusion Patterns

Excluded patterns:
- `node_modules`, `.git`, `__pycache__`
- `dist`, `build`, `target`
- `*.min.js`, `*.bundle.js`
- `.venv`, `venv`

## Stage 2: Parsing

### Language Detection

```python
def get_language(file_path: str) -> Optional[str]:
    ext = os.path.splitext(file_path)[1].lower()
    for lang, patterns in LANGUAGE_PATTERNS.items():
        if ext in patterns['extensions']:
            return lang
    return None
```

### Function Detection (Python)

```python
match = re.match(r'def\s+(\w+)\s*\(([^)]*)\)', stripped)
```

### Class Detection (Python)

```python
match = re.match(r'class\s+(\w+)(?:\(([^)]*)\))?:', stripped)
```

### Decorator Detection (Python)

```python
match = re.match(r'@(\w+)', stripped)
```

### JavaScript Function Detection

```python
# Three patterns:
# 1. function name()
# 2. const name = () => {}
# 3. const name = async () => {}
```

## Stage 3: Documentation Generation

### Module Grouping

Files are grouped by their parent directory:

```
captionhook/
├── app/
│   ├── api/
│   │   └── generate/
│   │       └── route.ts  → module: "api/generate"
│   ├── dashboard/         → module: "dashboard"
```

### Coverage Calculation

```python
# File coverage: has any comments?
files_documented = sum(1 for f in files if f['comment_lines'] > 0)
file_coverage = files_documented / total_files * 100

# Function coverage: has docstring?
documented_functions = sum(1 for f in files if f['functions'] and f['comment_lines'] > 0)
func_coverage = documented_functions / total_functions * 100

# Overall
overall = (file_coverage + func_coverage + class_coverage) / 3
```

### Coverage Ratings

| Rating | Threshold | Action |
|--------|-----------|--------|
| Excellent | 80%+ | Maintain level |
| Good | 60-80% | Improve gradually |
| Fair | 40-60% | Prioritize gaps |
| Poor | <40% | Needs significant work |

## Limitations

LegacyDocs uses regex parsing, not AST:
- Cannot detect function complexity
- Cannot track variable types accurately
- Cannot understand control flow
- Cannot generate deep semantic docs

Best for: understanding project structure, identifying undocumented areas
Not for: API reference, detailed behavior docs

## Future Enhancements

1. **AST-based parsing** — use `ast` module (Python), `babel-parser` (JS)
2. **API endpoint detection** — recognize route patterns
3. **Schema extraction** — TypeScript interfaces, Go structs
4. **Docstring generation** — suggest docstrings from code
5. **Diff-based updates** — only update changed files