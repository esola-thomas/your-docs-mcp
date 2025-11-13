# Validate Documentation Action

A reusable GitHub Actions composite action for validating markdown documentation against project standards.

## Features

- Validates YAML frontmatter in markdown files
- Checks markdown syntax and formatting
- Validates internal and external links
- Enforces line length limits
- Verifies code block language tags
- Checks content structure and quality

## Usage

### Basic Usage

```yaml
steps:
  - name: Checkout code
    uses: actions/checkout@v5

  - name: Validate documentation
    uses: ./.github/actions/validate-docs
```

### Advanced Usage

```yaml
steps:
  - name: Checkout code
    uses: actions/checkout@v5

  - name: Validate documentation
    uses: ./.github/actions/validate-docs
    with:
      paths: 'docs/ README.md CONTRIBUTING.md'
      python-version: '3.11'
      fail-on-warnings: 'false'
      generate-report: 'true'
      report-path: 'validation-report.md'
      upload-report: 'true'
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `paths` | Space-separated paths to markdown files or directories to validate | No | `docs/ README.md` |
| `python-version` | Python version to use | No | `3.11` |
| `fail-on-warnings` | Fail the validation if warnings are found | No | `false` |
| `generate-report` | Generate a validation report | No | `true` |
| `report-path` | Path to save the validation report | No | `validation-report.md` |
| `upload-report` | Upload the validation report as an artifact on failure | No | `true` |

## Outputs

| Output | Description |
|--------|-------------|
| `validation-status` | Status of the validation (passed/failed) |
| `critical-count` | Number of critical issues found |
| `warning-count` | Number of warnings found |

## Examples

### Validate Only Docs Folder

```yaml
- name: Validate documentation
  uses: ./.github/actions/validate-docs
  with:
    paths: 'docs/'
```

### Fail on Warnings

```yaml
- name: Validate documentation (strict)
  uses: ./.github/actions/validate-docs
  with:
    paths: 'docs/ README.md'
    fail-on-warnings: 'true'
```

### Custom Report Path

```yaml
- name: Validate documentation
  uses: ./.github/actions/validate-docs
  with:
    paths: 'docs/'
    report-path: 'reports/doc-validation.md'
```

### Use with Matrix Strategy

```yaml
jobs:
  validate-docs:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        docs-path: ['docs/guides/', 'docs/api/', 'docs/tutorials/']
    steps:
      - uses: actions/checkout@v5
      - uses: ./.github/actions/validate-docs
        with:
          paths: ${{ matrix.docs-path }}
```

## Requirements

- Python 3.11 or higher (configurable)
- PyYAML package (automatically installed)
- The `scripts/validate_docs.py` script must exist in the repository

## Validation Rules

The action validates the following aspects of markdown documentation:

### YAML Frontmatter
- Must have opening and closing `---` delimiters
- Must include required fields: `title`, `category`, `tags`, `order`
- Field types must be correct (string, array, integer)

### Headers
- Only one H1 header per document
- No skipped header levels (e.g., H1 → H3)
- Space required after `#` in headers

### Code Blocks
- All code blocks must have language specifiers
- Example: ` ```python ` instead of ` ``` `

### Line Length
- Lines should not exceed 100 characters (excluding code blocks and URLs)

### Links
- Internal links must use relative paths
- Internal links must point to existing files
- Link text should be descriptive (not "here" or "click here")

### Lists
- Consistent bullet characters throughout
- Proper indentation (multiples of 2 spaces)

## Troubleshooting

### Action Fails to Find validate_docs.py

Make sure the `scripts/validate_docs.py` file exists in your repository at the root level.

### Python Version Conflicts

If you need a different Python version, set the `python-version` input:

```yaml
- uses: ./.github/actions/validate-docs
  with:
    python-version: '3.12'
```

### Report Not Uploaded

The report is only uploaded when the validation fails. To always upload the report, modify the action or add a separate step.

## Contributing

To improve this action, edit the `.github/actions/validate-docs/action.yml` file.

## License

This action is part of the Markdown-MCP project.
