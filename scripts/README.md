# Documentation Scripts

This directory contains scripts for validating and maintaining project documentation.

## validate_docs.py

Comprehensive documentation validation script that checks markdown files against project standards.

### Features

- **YAML Frontmatter Validation**: Ensures all documentation has valid, complete frontmatter
- **Markdown Syntax Checking**: Validates header hierarchy, code blocks, lists, and formatting
- **Link Validation**: Checks internal links and identifies broken references
- **Line Length Enforcement**: Ensures lines don't exceed 100 characters (with exceptions)
- **Content Quality**: Validates document structure and completeness
- **Detailed Reports**: Provides actionable feedback with severity levels

### Usage

```bash
# Validate single file
python scripts/validate_docs.py docs/guides/getting-started.md

# Validate directory
python scripts/validate_docs.py docs/

# Validate multiple paths
python scripts/validate_docs.py docs/ README.md .github/CONTRIBUTING.md

# Generate detailed report
python scripts/validate_docs.py docs/ --report=validation-report.md

# Show only critical issues
python scripts/validate_docs.py docs/ --no-warnings
```

### Exit Codes

- `0`: Validation passed (no critical issues)
- `1`: Validation failed (critical issues found)

### Issue Severity Levels

**Critical (❌)**: Must fix before merge
- Missing or invalid YAML frontmatter
- Missing required fields
- Multiple H1 headers
- Skipped header levels
- Code blocks without language specifiers
- Broken internal links

**Warning (⚠️)**: Should fix
- Line length exceeded (>100 characters)
- Non-descriptive link text
- Missing table of contents
- Inconsistent list formatting
- Incorrect indentation

**Info (ℹ️)**: Optional improvements
- Unusual categories
- Missing optional sections
- Suggestions for better organization

### CI/CD Integration

The validation script runs automatically on pull requests through the GitHub Actions workflow:

```yaml
- name: Validate documentation
  run: |
    python scripts/validate_docs.py docs/ README.md .github/CONTRIBUTING.md
```

### Requirements

```bash
pip install pyyaml
```

### Examples

**Example 1: Validate all documentation**

```bash
$ python scripts/validate_docs.py docs/
Validating 15 markdown files...

✅ docs/guides/getting-started.md
❌ docs/guides/configuration.md (2 critical, 3 warnings)
✅ docs/api/endpoints.md

Summary:
- Total Files: 15
- Files Passed: 13
- Critical Issues: 2
- Warnings: 3
```

**Example 2: Check single file**

```bash
$ python scripts/validate_docs.py docs/guides/example.md

Validating 1 markdown files...

❌ docs/guides/example.md (1 critical, 0 warnings)
   ❌ CRITICAL: Code block missing language specifier
   Location: docs/guides/example.md:45
   Current: ```
   Fix: ```python (or appropriate language)

❌ Validation failed: Critical issues must be fixed
```

### Validation Checks

#### YAML Frontmatter

```yaml
---
title: "Document Title"          # Required, string
category: "Category"             # Required, string
tags: ["tag1", "tag2"]           # Required, array
order: 1                         # Required, integer
parent: "parent/path"            # Optional, string
description: "Description"       # Optional, string
---
```

#### Markdown Formatting

- One H1 (`#`) per document
- No skipped header levels
- Space after `#` in headers
- Code blocks with language specifiers
- Consistent list bullet characters
- 2-space indentation for nested lists
- Maximum 100 character line length

#### Links

- Internal links use relative paths
- Include `.md` extension
- Target files exist
- Descriptive link text (not "here" or "click")

#### Content Structure

- Clear introduction
- Table of contents (for >3 sections)
- Working code examples
- Related resources section

## Related Documentation

- [Documentation Standards](./.claude/DOCUMENTATION_STANDARDS.md) - Complete style guide
- [Contributing Guide](../.github/CONTRIBUTING.md) - Project contribution guidelines
- [Agent Templates](../.claude/agents/) - Claude Code agents for documentation tasks
  - `doc-creator.md` - Creating new documentation
  - `doc-editor.md` - Modifying existing documentation
  - `doc-validator.md` - Validating documentation

## Development

To modify or extend the validation script:

1. Edit `validate_docs.py`
2. Test on example documentation: `python scripts/validate_docs.py example/`
3. Run on main docs: `python scripts/validate_docs.py docs/`
4. Update this README if adding new features

### Adding New Validation Rules

Add new validation methods to the `DocumentValidator` class:

```python
def _validate_custom_rule(self, file_path: Path, lines: List[str],
                         result: ValidationResult) -> None:
    """Validate custom rule."""
    for i, line in enumerate(lines, 1):
        if condition:
            result.issues.append(ValidationIssue(
                severity=Severity.WARNING,
                file_path=str(file_path),
                line_number=i,
                issue="Description of issue",
                fix="How to fix it"
            ))
```

Then call it from `validate_file()`:

```python
self._validate_custom_rule(file_path, lines, result)
```

## Troubleshooting

**Issue**: Script not found
```bash
python: can't open file 'scripts/validate_docs.py': No such file or directory
```
**Solution**: Run from project root directory

**Issue**: ModuleNotFoundError: No module named 'yaml'
```bash
pip install pyyaml
```

**Issue**: Permission denied
```bash
chmod +x scripts/validate_docs.py
```

## Future Enhancements

Potential future features:

- Auto-fix mode (`--fix`) to automatically correct common issues
- Spell checking integration
- Link checker for external URLs
- Image validation
- Anchor link validation
- Custom rule configuration via config file
- JSON output format for tool integration
- Incremental validation (only changed files)
- Performance metrics and benchmarking

## License

Part of the Hierarchical Documentation MCP Server project.
