---
title: CI/CD Pipeline Integration
category: Development
tags: ["ci-cd", "github-actions", "azure-devops", "automation", "documentation"]
order: 5
---

# CI/CD Pipeline Integration

This document explains how to integrate documentation validation into your CI/CD pipelines using reusable templates for both GitHub Actions and Azure DevOps.

## Overview

The Markdown-MCP project provides reusable pipeline components that can be used just like `actions/setup-python@v6` in GitHub Actions or standard Azure DevOps tasks. These components wrap the `scripts/validate_docs.py` validation script in a convenient, parameterized interface.

## Quick Start

### GitHub Actions

```yaml
steps:
  - uses: actions/checkout@v5
  - uses: ./.github/actions/validate-docs
    with:
      paths: 'docs/ README.md'
```

### Azure DevOps

```yaml
steps:
  - checkout: self
  - template: pipelines/templates/validate-docs.yml
    parameters:
      paths: 'docs/ README.md'
```

## Platform Comparison

| Feature | GitHub Actions | Azure DevOps |
|---------|----------------|--------------|
| **Component Type** | Composite Action | Pipeline Template |
| **Location** | `.github/actions/validate-docs/` | `pipelines/templates/` |
| **Usage Syntax** | `uses: ./.github/actions/validate-docs` | `template: pipelines/templates/validate-docs.yml` |
| **Parameters** | Passed via `with:` | Passed via `parameters:` |
| **Python Setup** | `actions/setup-python@v6` | `UsePythonVersion@0` |
| **Artifact Upload** | `actions/upload-artifact@v5` | `PublishPipelineArtifact@1` |

## GitHub Actions Integration

### Basic Setup

1. **Copy the action** (if not already present):
   ```bash
   # The action is already included in this repository at:
   # .github/actions/validate-docs/
   ```

2. **Use in your workflow**:
   ```yaml
   # .github/workflows/docs.yml
   name: Documentation Validation

   on: [push, pull_request]

   jobs:
     validate:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v5
         - uses: ./.github/actions/validate-docs
   ```

### Advanced Configuration

```yaml
jobs:
  validate-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5

      - name: Validate documentation
        uses: ./.github/actions/validate-docs
        with:
          # Paths to validate (space-separated)
          paths: 'docs/ README.md CONTRIBUTING.md'

          # Python version to use
          python-version: '3.11'

          # Fail on warnings (not just critical issues)
          fail-on-warnings: 'false'

          # Generate validation report
          generate-report: 'true'

          # Report output path
          report-path: 'validation-report.md'

          # Upload report as artifact on failure
          upload-report: 'true'
```

### Matrix Strategy

Validate different documentation sections in parallel:

```yaml
jobs:
  validate-sections:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include:
          - path: 'docs/guides/'
            name: 'Guides'
          - path: 'docs/api/'
            name: 'API'
          - path: 'docs/tutorials/'
            name: 'Tutorials'

    steps:
      - uses: actions/checkout@v5
      - uses: ./.github/actions/validate-docs
        with:
          paths: ${{ matrix.path }}
          report-path: 'validation-${{ matrix.name }}.md'
```

### Available Inputs

| Input | Description | Default | Required |
|-------|-------------|---------|----------|
| `paths` | Space-separated paths to validate | `docs/ README.md` | No |
| `python-version` | Python version to use | `3.11` | No |
| `fail-on-warnings` | Fail on warnings (not just critical) | `false` | No |
| `generate-report` | Generate validation report | `true` | No |
| `report-path` | Report output path | `validation-report.md` | No |
| `upload-report` | Upload report as artifact on failure | `true` | No |

### Available Outputs

| Output | Description |
|--------|-------------|
| `validation-status` | Status of validation (`passed`/`failed`) |
| `critical-count` | Number of critical issues found |
| `warning-count` | Number of warnings found |

## Azure DevOps Integration

### Basic Setup

1. **Copy the template** (if not already present):
   ```bash
   # The template is already included in this repository at:
   # pipelines/templates/validate-docs.yml
   ```

2. **Create your pipeline**:
   ```yaml
   # azure-pipelines.yml
   trigger:
     - main

   pool:
     vmImage: 'ubuntu-latest'

   stages:
     - stage: Validate
       jobs:
         - job: ValidateDocs
           steps:
             - checkout: self
             - template: pipelines/templates/validate-docs.yml
   ```

### Advanced Configuration

```yaml
stages:
  - stage: Validate
    jobs:
      - job: ValidateDocs
        displayName: 'Validate Documentation'
        steps:
          - checkout: self

          - template: pipelines/templates/validate-docs.yml
            parameters:
              # Paths to validate (space-separated)
              paths: 'docs/ README.md CONTRIBUTING.md'

              # Python version to use
              pythonVersion: '3.11'

              # Fail on warnings (not just critical issues)
              failOnWarnings: false

              # Generate validation report
              generateReport: true

              # Report output path
              reportPath: 'validation-report.md'

              # Publish report as artifact on failure
              publishReport: true
```

### Multiple Validation Jobs

Validate different sections or apply different rules:

```yaml
stages:
  - stage: Validate
    jobs:
      # Lenient validation for development
      - job: ValidateDev
        condition: ne(variables['Build.SourceBranch'], 'refs/heads/main')
        steps:
          - checkout: self
          - template: pipelines/templates/validate-docs.yml
            parameters:
              paths: 'docs/'
              failOnWarnings: false

      # Strict validation for production
      - job: ValidateProduction
        condition: eq(variables['Build.SourceBranch'], 'refs/heads/main')
        steps:
          - checkout: self
          - template: pipelines/templates/validate-docs.yml
            parameters:
              paths: 'docs/ README.md'
              failOnWarnings: true
```

### Available Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `paths` | string | `docs/ README.md` | Space-separated paths to validate |
| `pythonVersion` | string | `3.11` | Python version to use |
| `failOnWarnings` | boolean | `false` | Fail on warnings (not just critical) |
| `generateReport` | boolean | `true` | Generate validation report |
| `reportPath` | string | `validation-report.md` | Report output path |
| `publishReport` | boolean | `true` | Publish report as artifact on failure |

## Validation Rules

Both platform integrations use the same `scripts/validate_docs.py` script, which validates:

### YAML Frontmatter
- Required fields: `title`, `category`, `tags`, `order`
- Correct field types
- Valid category values

### Markdown Structure
- Single H1 header
- No skipped header levels
- Proper header formatting

### Code Blocks
- Language specifiers required
- Example: ` ```python ` not ` ``` `

### Line Length
- Maximum 100 characters (excluding code blocks and URLs)

### Links
- Internal links use relative paths
- Internal links point to existing files
- Descriptive link text (not "here" or "click here")

### Lists
- Consistent bullet characters
- Proper indentation (multiples of 2 spaces)

## Best Practices

### 1. Validate on Every Push

```yaml
# GitHub Actions
on:
  push:
    paths:
      - 'docs/**'
      - '*.md'

# Azure DevOps
trigger:
  paths:
    include:
      - docs/**
      - '*.md'
```

### 2. Use Strict Mode for Main Branch

```yaml
# GitHub Actions
- uses: ./.github/actions/validate-docs
  with:
    fail-on-warnings: ${{ github.ref == 'refs/heads/main' }}

# Azure DevOps
- template: pipelines/templates/validate-docs.yml
  parameters:
    failOnWarnings: ${{ eq(variables['Build.SourceBranch'], 'refs/heads/main') }}
```

### 3. Always Generate Reports

Keep `generate-report: true` (default) to get detailed validation feedback.

### 4. Cache Dependencies

```yaml
# GitHub Actions (already included in action)
- uses: actions/setup-python@v6
  with:
    python-version: '3.11'
    cache: 'pip'

# Azure DevOps
- task: Cache@2
  inputs:
    key: 'python | "$(Agent.OS)" | requirements.txt'
    path: $(PIP_CACHE_DIR)
```

### 5. Validate in Parallel

Use matrix strategies to validate different sections concurrently and speed up the pipeline.

## Running Locally

Before committing, test validation locally:

```bash
# Install dependencies
pip install pyyaml

# Validate all documentation
python scripts/validate_docs.py docs/ README.md

# Validate with report
python scripts/validate_docs.py docs/ --report=validation-report.md

# Validate without warnings
python scripts/validate_docs.py docs/ --no-warnings
```

## Troubleshooting

### Action/Template Not Found

**GitHub Actions:**
```text
Error: Unable to resolve action ./.github/actions/validate-docs
```
**Solution:** Ensure the action exists at `.github/actions/validate-docs/action.yml`

**Azure DevOps:**
```text
Error: Template file not found: pipelines/templates/validate-docs.yml
```
**Solution:** Ensure the template exists at `pipelines/templates/validate-docs.yml`

### Python Version Issues

**Problem:** Need a specific Python version

**Solution:**
```yaml
# GitHub Actions
with:
  python-version: '3.12'

# Azure DevOps
parameters:
  pythonVersion: '3.12'
```

### Validation Script Not Found

**Problem:**
```text
Error: scripts/validate_docs.py not found
```

**Solution:** Ensure `scripts/validate_docs.py` exists in repository root

### Report Not Generated

**Problem:** Report file not created

**Solution:** Check that `generate-report` is `true` and the script has write permissions

## Migration Guide

### From Direct Script Calls

**Before:**
```yaml
- name: Validate docs
  run: |
    pip install pyyaml
    python scripts/validate_docs.py docs/
```

**After:**
```yaml
- uses: ./.github/actions/validate-docs
  with:
    paths: 'docs/'
```

### From Custom Validation Steps

Replace custom validation steps with the reusable templates to ensure consistency across projects.

## Examples

Complete working examples are available in:

- **GitHub Actions:** `pipelines/examples/github-actions-example.yml`
- **Azure DevOps:** `pipelines/examples/azure-pipelines-example.yml`

## Related Documentation

- [GitHub Actions Documentation](../.github/actions/validate-docs/README.md)
- [Azure DevOps Templates Documentation](../pipelines/README.md)
- [Validation Script Documentation](../scripts/validate_docs.py)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the example pipelines
3. Open an issue in the repository

## Contributing

To improve the pipeline templates:
1. Edit `.github/actions/validate-docs/action.yml` for GitHub Actions
2. Edit `pipelines/templates/validate-docs.yml` for Azure DevOps
3. Update this documentation
4. Submit a pull request
