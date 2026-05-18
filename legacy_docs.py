#!/usr/bin/env python3
"""
LegacyDocs - Auto-generate documentation from code

Analyzes codebase structure, extracts functions/classes/modules,
generates comprehensive markdown documentation without requiring docstrings.
"""

import argparse
import os
import re
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# === LANGUAGE SUPPORT ===

LANGUAGE_PATTERNS = {
    'python': {
        'extensions': ['.py'],
        'function': r'def\s+(\w+)\s*\(([^)]*)\)',
        'class': r'class\s+(\w+)(?:\([^)]*\))?:',
        'import': r'^(?:import|from)\s+(\S+)',
        'decorator': r'@(\w+)',
        'docstring': r'"""([^"]*)"""',
    },
    'javascript': {
        'extensions': ['.js', '.jsx', '.mjs'],
        'function': r'(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>|(\w+)\s*\([^)]*\)\s*\{)',
        'class': r'class\s+(\w+)',
        'import': r'(?:import|require)\s*\(?[\'"]([^\'"]+)[\'"]',
        'export': r'export\s+(?:default\s+)?(?:function|class|const|async)',
    },
    'typescript': {
        'extensions': ['.ts', '.tsx', '.d.ts'],
        'function': r'(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*[=>]|(\w+)\s*\([^)]*\)\s*[:{])',
        'class': r'class\s+(\w+)',
        'import': r'import\s+(?:{[^}]+}|\w+)\s+from\s+[\'"]([^\'"]+)[\'"]',
        'interface': r'interface\s+(\w+)',
        'type': r'type\s+(\w+)\s*=',
    },
    'go': {
        'extensions': ['.go'],
        'function': r'func\s+(?:\([^)]+\)\s+)?(\w+)\s*\(',
        'struct': r'type\s+(\w+)\s+struct\s*\{',
        'import': r'import\s+(?:"([^"]+)")?',
    },
    'rust': {
        'extensions': ['.rs'],
        'function': r'fn\s+(\w+)\s*(?:<[^>]*>)?\s*\(',
        'struct': r'struct\s+(\w+)',
        'impl': r'impl\s+(?:[^{]+\s+for\s+)?(\w+)',
        'use': r'use\s+([^;]+)',
    },
    'php': {
        'extensions': ['.php'],
        'function': r'function\s+(\w+)\s*\(',
        'class': r'class\s+(\w+)',
        'namespace': r'namespace\s+([^;]+)',
        'use': r'use\s+([^;]+)',
    },
}

EXCLUDE_PATTERNS = [
    'node_modules', '.git', '__pycache__', '.venv', 'venv',
    'dist', 'build', 'target', 'coverage', '.next', '.nuxt',
    '*.min.js', '*.bundle.js', '.cache', '.parcel-cache'
]

# === FILE ANALYSIS ===

def should_exclude(path: str) -> bool:
    """Check if path should be excluded."""
    path_lower = path.lower()
    for pattern in EXCLUDE_PATTERNS:
        if pattern.startswith('*'):
            if path_lower.endswith(pattern[1:]):
                return True
        elif pattern in path_lower:
            return True
    return False

def get_language(file_path: str) -> Optional[str]:
    """Detect language from file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    for lang, patterns in LANGUAGE_PATTERNS.items():
        if ext in patterns['extensions']:
            return lang
    return None

def count_lines(file_path: str) -> Tuple[int, int, int]:
    """Count total, code, and comment lines."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        total = len(lines)
        code = 0
        comments = 0
        in_multiline = False

        for line in lines:
            stripped = line.strip()

            if not stripped:
                continue

            # Multiline strings/comments
            if '"""' in stripped or "'''" in stripped:
                in_multiline = not in_multiline
                comments += 1
                continue

            if in_multiline:
                comments += 1
                continue

            # Single line comments
            if stripped.startswith('#') or stripped.startswith('//'):
                comments += 1
                continue

            code += 1

        return total, code, comments
    except Exception:
        return 0, 0, 0

def parse_python_content(content: str, file_path: str) -> Dict:
    """Parse Python file content."""
    functions = []
    classes = []
    imports = []
    decorators = []

    lines = content.split('\n')

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Decorator
        match = re.match(r'@(\w+)', stripped)
        if match:
            decorators.append({
                'name': match.group(1),
                'line': i + 1
            })
            continue

        # Function
        match = re.match(r'def\s+(\w+)\s*\(([^)]*)\)', stripped)
        if match:
            func_name = match.group(1)
            params = match.group(2).strip()
            # Get following lines for docstring hint
            doc = ''
            if i + 1 < len(lines) and '"""' in lines[i + 1]:
                doc = 'Has docstring'
            functions.append({
                'name': func_name,
                'line': i + 1,
                'params': params,
                'decorators': [d['name'] for d in decorators if d['line'] >= i - 3],
                'doc': doc
            })
            decorators = []
            continue

        # Class
        match = re.match(r'class\s+(\w+)(?:\(([^)]*)\))?:', stripped)
        if match:
            classes.append({
                'name': match.group(1),
                'line': i + 1,
                'bases': match.group(2) or '',
                'decorators': [d['name'] for d in decorators if d['line'] >= i - 3]
            })
            decorators = []
            continue

        # Import
        match = re.match(r'^(?:import|from)\s+(\S+)', stripped)
        if match:
            imports.append({
                'module': match.group(1),
                'line': i + 1
            })

    return {
        'functions': functions,
        'classes': classes,
        'imports': imports
    }

def parse_javascript_content(content: str, file_path: str) -> Dict:
    """Parse JavaScript/TypeScript file content."""
    functions = []
    classes = []
    imports = []
    exports = []

    lines = content.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Import
        match = re.match(r'(?:import|require)\s*\(?[\'"]([^\'"]+)[\'"]', line)
        if match:
            imports.append({
                'module': match.group(1),
                'line': i + 1
            })
            i += 1
            continue

        # Function declaration
        match = re.match(r'function\s+(\w+)\s*\(([^)]*)\)', line)
        if match:
            functions.append({
                'name': match.group(1),
                'line': i + 1,
                'params': match.group(2).strip()
            })
            i += 1
            continue

        # Arrow function or const/let function
        match = re.match(r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*(?:=>)?', line)
        if match:
            functions.append({
                'name': match.group(1),
                'line': i + 1,
                'params': match.group(2).strip() if len(match.groups()) > 1 else ''
            })
            i += 1
            continue

        # Class
        match = re.match(r'class\s+(\w+)', line)
        if match:
            classes.append({
                'name': match.group(1),
                'line': i + 1
            })
            i += 1
            continue

        # Export
        if line.startswith('export'):
            exports.append({
                'type': 'function' if 'function' in line else 'class' if 'class' in line else 'const',
                'line': i + 1
            })

        i += 1

    return {
        'functions': functions,
        'classes': classes,
        'imports': imports,
        'exports': exports
    }

def parse_go_content(content: str, file_path: str) -> Dict:
    """Parse Go file content."""
    functions = []
    structs = []
    imports = []

    lines = content.split('\n')

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Import
        match = re.search(r'"([^"]+)"', stripped)
        if match and 'import' in stripped:
            imports.append({
                'module': match.group(1),
                'line': i + 1
            })
            continue

        # Function
        match = re.match(r'func\s+(?:\([^)]+\)\s+)?(\w+)\s*\(', stripped)
        if match:
            functions.append({
                'name': match.group(1),
                'line': i + 1
            })
            continue

        # Struct
        match = re.match(r'type\s+(\w+)\s+struct\s*\{', stripped)
        if match:
            structs.append({
                'name': match.group(1),
                'line': i + 1
            })

    return {
        'functions': functions,
        'structs': structs,
        'imports': imports
    }

def parse_rust_content(content: str, file_path: str) -> Dict:
    """Parse Rust file content."""
    functions = []
    structs = []
    imports = []

    lines = content.split('\n')

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Use
        match = re.match(r'use\s+([^;]+)', stripped)
        if match:
            imports.append({
                'module': match.group(1).strip(),
                'line': i + 1
            })
            continue

        # Function
        match = re.match(r'fn\s+(\w+)', stripped)
        if match:
            functions.append({
                'name': match.group(1),
                'line': i + 1
            })
            continue

        # Struct
        match = re.match(r'struct\s+(\w+)', stripped)
        if match:
            structs.append({
                'name': match.group(1),
                'line': i + 1
            })

    return {
        'functions': functions,
        'structs': structs,
        'imports': imports
    }

def parse_php_content(content: str, file_path: str) -> Dict:
    """Parse PHP file content."""
    functions = []
    classes = []
    imports = []

    lines = content.split('\n')

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Namespace
        match = re.match(r'namespace\s+([^;]+)', stripped)
        if match:
            imports.append({
                'module': match.group(1),
                'line': i + 1
            })
            continue

        # Use
        match = re.match(r'use\s+([^;]+)', stripped)
        if match:
            imports.append({
                'module': match.group(1),
                'line': i + 1
            })
            continue

        # Function
        match = re.match(r'function\s+(\w+)\s*\(', stripped)
        if match:
            functions.append({
                'name': match.group(1),
                'line': i + 1
            })
            continue

        # Class
        match = re.match(r'class\s+(\w+)', stripped)
        if match:
            classes.append({
                'name': match.group(1),
                'line': i + 1
            })

    return {
        'functions': functions,
        'classes': classes,
        'imports': imports
    }

def parse_content(content: str, file_path: str) -> Dict:
    """Parse file content based on language."""
    language = get_language(file_path)

    if language == 'python':
        return parse_python_content(content, file_path)
    elif language in ['javascript', 'typescript']:
        return parse_javascript_content(content, file_path)
    elif language == 'go':
        return parse_go_content(content, file_path)
    elif language == 'rust':
        return parse_rust_content(content, file_path)
    elif language == 'php':
        return parse_php_content(content, file_path)

    return {'functions': [], 'classes': [], 'imports': []}

# === PROJECT ANALYSIS ===

def analyze_file(file_path: str) -> Dict:
    """Analyze a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        total_lines, code_lines, comment_lines = count_lines(file_path)
        parsed = parse_content(content, file_path)
        language = get_language(file_path)

        return {
            'path': file_path,
            'language': language,
            'total_lines': total_lines,
            'code_lines': code_lines,
            'comment_lines': comment_lines,
            'functions': parsed.get('functions', []),
            'classes': parsed.get('classes', []),
            'imports': parsed.get('imports', []),
            'structs': parsed.get('structs', []),
            'exports': parsed.get('exports', [])
        }
    except Exception as e:
        return {'error': str(e), 'path': file_path}

def analyze_project(root_path: str) -> Dict:
    """Analyze entire project."""
    root_path = os.path.expanduser(root_path)
    if not os.path.exists(root_path):
        return {'error': f'Path not found: {root_path}'}

    files = []
    for ext_pattern in ['*.py', '*.js', '*.jsx', '*.ts', '*.tsx', '*.go', '*.rs', '*.php']:
        for file_path in Path(root_path).rglob(ext_pattern):
            if not should_exclude(str(file_path)):
                files.append(str(file_path))

    results = []
    for file_path in files:
        result = analyze_file(file_path)
        if 'error' not in result:
            results.append(result)

    return {
        'project': os.path.basename(root_path),
        'path': root_path,
        'files': results,
        'total_files': len(results),
        'analyzed_at': datetime.now().isoformat()
    }

# === DOCUMENTATION GENERATION ===

def generate_module_docs(files: List[Dict], module_name: str) -> str:
    """Generate documentation for a module."""
    lines = [
        f"# {module_name}",
        "",
        f"Auto-generated documentation",
        "",
    ]

    # Group by file
    by_file = {}
    for f in files:
        file_path = f['path']
        rel = os.path.basename(os.path.dirname(file_path)) or 'root'
        if rel not in by_file:
            by_file[rel] = []
        by_file[rel].append(f)

    for file_group, file_list in by_file.items():
        lines.append(f"## {file_group}")
        lines.append("")

        for file_info in file_list:
            rel_path = os.path.relpath(file_info['path'], module_name)
            lines.append(f"### `{rel_path}`")
            lines.append("")
            lines.append(f"**Language:** {file_info['language']}")
            lines.append(f"**Lines:** {file_info['code_lines']} code, {file_info['comment_lines']} comments")
            lines.append("")

            # Functions
            if file_info['functions']:
                lines.append("#### Functions")
                lines.append("")
                for func in file_info['functions'][:10]:  # Limit to 10
                    params = f"({func.get('params', '')})" if 'params' in func else ''
                    dec = f" `@{func['decorators'][0]}`" if func.get('decorators') else ''
                    lines.append(f"- `{func['name']}{params}`{dec}")
                lines.append("")

            # Classes
            if file_info['classes']:
                lines.append("#### Classes")
                lines.append("")
                for cls in file_info['classes'][:10]:
                    dec = f" `@{cls['decorators'][0]}`" if cls.get('decorators') else ''
                    lines.append(f"- `{cls['name']}`{dec}")
                lines.append("")

            # Imports
            if file_info['imports']:
                lines.append(f"**Imports:** {', '.join(i['module'] for i in file_info['imports'][:5])}")
                lines.append("")

            lines.append("---")
            lines.append("")

    return '\n'.join(lines)

def calculate_coverage(files: List[Dict]) -> Dict:
    """Calculate documentation coverage score."""
    total_files = len(files)
    total_functions = 0
    total_classes = 0
    documented_functions = 0
    documented_classes = 0
    total_code_lines = 0

    for file_info in files:
        total_code_lines += file_info['code_lines']
        total_functions += len(file_info['functions'])
        total_classes += len(file_info['classes'])

        # Files with docstrings/comments count as documented
        if file_info['comment_lines'] > 0:
            documented_functions += len(file_info['functions'])
            documented_classes += len(file_info['classes'])

    # Simple coverage: files with any comments / total files
    files_documented = sum(1 for f in files if f['comment_lines'] > 0)
    file_coverage = (files_documented / total_files * 100) if total_files > 0 else 0

    # Function coverage: functions with docstrings
    func_coverage = (documented_functions / total_functions * 100) if total_functions > 0 else 0

    # Class coverage
    class_coverage = (documented_classes / total_classes * 100) if total_classes > 0 else 0

    overall = (file_coverage + func_coverage + class_coverage) / 3

    return {
        'total_files': total_files,
        'files_documented': files_documented,
        'file_coverage': round(file_coverage, 1),
        'total_functions': total_functions,
        'documented_functions': documented_functions,
        'func_coverage': round(func_coverage, 1),
        'total_classes': total_classes,
        'documented_classes': documented_classes,
        'class_coverage': round(class_coverage, 1),
        'overall_coverage': round(overall, 1),
        'total_code_lines': total_code_lines
    }

def format_coverage_markdown(coverage: Dict) -> str:
    """Format coverage report as markdown."""
    rating = "Excellent" if coverage['overall_coverage'] >= 80 else \
             "Good" if coverage['overall_coverage'] >= 60 else \
             "Fair" if coverage['overall_coverage'] >= 40 else "Poor"

    lines = [
        "# Documentation Coverage Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|---------|-------|",
        f"| Total Files | {coverage['total_files']} |",
        f"| Files Documented | {coverage['files_documented']} |",
        f"| File Coverage | {coverage['file_coverage']}% |",
        f"| Total Functions | {coverage['total_functions']} |",
        f"| Functions Documented | {coverage['documented_functions']} |",
        f"| Function Coverage | {coverage['func_coverage']}% |",
        f"| Total Classes | {coverage['total_classes']} |",
        f"| Classes Documented | {coverage['documented_classes']} |",
        f"| Class Coverage | {coverage['class_coverage']}% |",
        f"| **Overall Coverage** | **{coverage['overall_coverage']}%** |",
        f"| Rating | {rating} |",
        "",
        f"Total code lines: {coverage['total_code_lines']:,}",
        "",
        f"_{rating} coverage - {'maintain current level' if rating == 'Excellent' else 'needs improvement'}_"
    ]

    return '\n'.join(lines)

def generate_project_readme(project_data: Dict, coverage: Dict = None) -> str:
    """Generate project README.md."""
    project_name = project_data['project']
    total_files = project_data['total_files']

    lines = [
        f"# {project_name}",
        "",
        f"Auto-generated documentation ({datetime.now().strftime('%Y-%m-%d')})",
        "",
        "## Project Overview",
        "",
        f"- **Files Analyzed:** {total_files}",
        f"- **Language:** Multi-language",
        "",
        "## Modules",
        ""
    ]

    # Group files by top-level directory
    modules = {}
    for file_info in project_data['files']:
        path = file_info['path']
        parts = path.split(os.sep)
        if len(parts) > 2:
            module = parts[-2]
            if module not in modules:
                modules[module] = []
            modules[module].append(file_info)

    for module, files in sorted(modules.items()):
        file_count = len(files)
        total_loc = sum(f['code_lines'] for f in files)
        func_count = sum(len(f['functions']) for f in files)
        class_count = sum(len(f['classes']) for f in files)
        lines.append(f"- **{module}/** — {file_count} files, {total_loc:,} LOC, {func_count} functions, {class_count} classes")

    if coverage:
        lines.append("")
        lines.append("## Documentation Coverage")
        lines.append("")
        lines.append(f"**Overall:** {coverage['overall_coverage']}% documented")
        rating = "Excellent" if coverage['overall_coverage'] >= 80 else \
                 "Good" if coverage['overall_coverage'] >= 60 else \
                 "Fair" if coverage['overall_coverage'] >= 40 else "Poor"
        lines.append(f"**Status:** {rating}")

    lines.append("")
    lines.append("---")
    lines.append("*Auto-generated by LegacyDocs*")

    return '\n'.join(lines)

# === OUTPUT ===

def save_docs(content: str, file_path: str) -> bool:
    """Save documentation to file."""
    try:
        os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error saving {file_path}: {e}")
        return False

def send_telegram(message: str) -> bool:
    """Send message to Telegram."""
    try:
        import requests
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')

        if not bot_token or not chat_id:
            return False

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        response = requests.post(url, json={
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }, timeout=30)
        return response.status_code == 200
    except Exception:
        return False

# === MAIN ===

def main():
    parser = argparse.ArgumentParser(description='LegacyDocs - Auto-generate documentation from code')
    parser.add_argument('--path', '-p', required=True, help='Project path to analyze')
    parser.add_argument('--output', '-o', default='./docs', help='Output directory')
    parser.add_argument('--coverage', '-c', action='store_true', help='Generate coverage report')
    parser.add_argument('--readme', '-r', action='store_true', help='Generate README.md')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    print(f"Analyzing: {args.path}")
    project_data = analyze_project(args.path)

    if 'error' in project_data:
        print(f"ERROR: {project_data['error']}")
        sys.exit(1)

    if args.json:
        print(json.dumps(project_data, indent=2))
        return

    # Generate coverage if requested
    if args.coverage:
        coverage = calculate_coverage(project_data['files'])
        coverage_md = format_coverage_markdown(coverage)
        print(f"\n{coverage_md}")

        coverage_path = os.path.join(args.output, 'COVERAGE.md')
        if save_docs(coverage_md, coverage_path):
            print(f"Coverage report saved to: {coverage_path}")

    # Generate README if requested
    if args.readme:
        coverage = calculate_coverage(project_data['files']) if args.coverage else None
        readme = generate_project_readme(project_data, coverage)
        readme_path = os.path.join(args.output, 'README.md')
        if save_docs(readme, readme_path):
            print(f"README saved to: {readme_path}")

    # Generate module docs
    modules = {}
    for file_info in project_data['files']:
        path = file_info['path']
        parts = path.split(os.sep)
        if len(parts) > 2:
            module = parts[-2]
            if module not in modules:
                modules[module] = []
            modules[module].append(file_info)

    docs_generated = 0
    for module, files in sorted(modules.items()):
        module_docs = generate_module_docs(files, module)
        module_path = os.path.join(args.output, f"{module}.md")
        if save_docs(module_docs, module_path):
            docs_generated += 1
            print(f"Generated: {module_path}")

    print(f"\nDone! Generated {docs_generated} module documentation files.")

    # Notify via Telegram
    msg = f"📄 *LegacyDocs Report*\n\nProject: `{project_data['project']}`\nFiles: {project_data['total_files']}\nModules: {len(modules)}"
    if args.coverage:
        coverage = calculate_coverage(project_data['files'])
        msg += f"\nCoverage: {coverage['overall_coverage']}%"
    send_telegram(msg)

if __name__ == '__main__':
    main()