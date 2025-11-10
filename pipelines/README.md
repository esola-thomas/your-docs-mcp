# Azure DevOps Pipeline Templates

This directory contains reusable Azure DevOps pipeline templates for common CI/CD tasks.

## Available Templates

### validate-docs.yml

Validates markdown documentation against project standards.

## Usage

### Basic Usage

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
        displayName: 'Validate Documentation'
        steps:
          - checkout: self
          - template: pipelines/templates/validate-docs.yml
```

### Advanced Usage with Parameters

```yaml
# azure-pipelines.yml
trigger:
  - main
  - develop

pool:
  vmImage: 'ubuntu-latest'

stages:
  - stage: Validate
    jobs:
      - job: ValidateDocs
        displayName: 'Validate Documentation'
        steps:
          - checkout: self

          - template: pipelines/templates/validate-docs.yml
            parameters:
              paths: 'docs/ README.md CONTRIBUTING.md'
              pythonVersion: '3.11'
              failOnWarnings: false
              generateReport: true
              reportPath: 'validation-report.md'
              publishReport: true
```

### Multiple Documentation Validations

```yaml
# azure-pipelines.yml
stages:
  - stage: Validate
    jobs:
      - job: ValidateGuideDocs
        displayName: 'Validate Guide Documentation'
        steps:
          - checkout: self
          - template: pipelines/templates/validate-docs.yml
            parameters:
              paths: 'docs/guides/'
              failOnWarnings: true

      - job: ValidateAPIDocs
        displayName: 'Validate API Documentation'
        steps:
          - checkout: self
          - template: pipelines/templates/validate-docs.yml
            parameters:
              paths: 'docs/api/'
              failOnWarnings: false
```

## Template Parameters

### validate-docs.yml

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `paths` | string | `docs/ README.md` | Space-separated paths to markdown files or directories to validate |
| `pythonVersion` | string | `3.11` | Python version to use |
| `failOnWarnings` | boolean | `false` | Fail the validation if warnings are found |
| `generateReport` | boolean | `true` | Generate a validation report |
| `reportPath` | string | `validation-report.md` | Path to save the validation report |
| `publishReport` | boolean | `true` | Publish report as pipeline artifact on failure |

## Complete Example Pipeline

```yaml
# azure-pipelines.yml
name: $(Date:yyyyMMdd)$(Rev:.r)

trigger:
  branches:
    include:
      - main
      - develop
      - feature/*
  paths:
    include:
      - docs/**
      - README.md
      - scripts/validate_docs.py

pr:
  branches:
    include:
      - main
      - develop
  paths:
    include:
      - docs/**
      - README.md

pool:
  vmImage: 'ubuntu-latest'

stages:
  - stage: Validate
    displayName: 'Validation Stage'
    jobs:
      - job: ValidateDocumentation
        displayName: 'Validate Markdown Documentation'
        steps:
          - checkout: self
            displayName: 'Checkout Repository'

          - template: pipelines/templates/validate-docs.yml
            parameters:
              paths: 'docs/ README.md'
              pythonVersion: '3.11'
              failOnWarnings: false
              generateReport: true
              publishReport: true

      - job: ValidateStrict
        displayName: 'Strict Validation (Fail on Warnings)'
        condition: eq(variables['Build.SourceBranch'], 'refs/heads/main')
        steps:
          - checkout: self

          - template: pipelines/templates/validate-docs.yml
            parameters:
              paths: 'docs/'
              pythonVersion: '3.11'
              failOnWarnings: true
              generateReport: true

  - stage: Deploy
    displayName: 'Deploy Documentation'
    dependsOn: Validate
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    jobs:
      - job: DeployDocs
        displayName: 'Deploy to Documentation Site'
        steps:
          - script: echo "Deploy documentation here"
            displayName: 'Deploy'
```

## Running Locally

To test the validation locally before committing:

```bash
# Install dependencies
pip install pyyaml

# Run validation
python scripts/validate_docs.py docs/ README.md

# Run with report generation
python scripts/validate_docs.py docs/ --report=validation-report.md

# Run without warnings
python scripts/validate_docs.py docs/ --no-warnings
```

## Validation Rules

See the [validate_docs.py script documentation](../scripts/validate_docs.py) for detailed information about validation rules.

## Troubleshooting

### Template Not Found

Make sure the template path is correct and relative to the repository root:

```yaml
- template: pipelines/templates/validate-docs.yml  # Correct
- template: templates/validate-docs.yml            # Incorrect
```

### Python Version Issues

If you need a specific Python version, set the `pythonVersion` parameter:

```yaml
- template: pipelines/templates/validate-docs.yml
  parameters:
    pythonVersion: '3.12'
```

### Validation Script Not Found

Ensure `scripts/validate_docs.py` exists in your repository at the root level.

## Creating Additional Templates

To create new reusable templates:

1. Create a new YAML file in `pipelines/templates/`
2. Define parameters at the top of the file
3. Define steps using the parameters
4. Document the template in this README

Example template structure:

```yaml
# pipelines/templates/my-template.yml
parameters:
  - name: myParameter
    type: string
    default: 'defaultValue'

steps:
  - script: echo "Parameter value: ${{ parameters.myParameter }}"
    displayName: 'Use Parameter'
```

## Contributing

To improve these templates, edit the files in `pipelines/templates/` and update this documentation accordingly.

## Resources

- [Azure DevOps Templates Documentation](https://docs.microsoft.com/en-us/azure/devops/pipelines/process/templates)
- [Azure DevOps YAML Schema Reference](https://docs.microsoft.com/en-us/azure/devops/pipelines/yaml-schema)
- [PyYAML Documentation](https://pyyaml.org/wiki/PyYAMLDocumentation)
