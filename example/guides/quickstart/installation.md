---
title: "Installation Guide"
tags: [quickstart, installation, setup, beginner]
category: "Guides"
order: 1
---

# Installation Guide

Welcome! This guide will help you install and set up the application quickly.

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.9 or higher
- pip (Python package installer)
- Git (optional, for installing from source)

## Installation Methods

### Method 1: Install from PyPI (Recommended)

The easiest way to install is using pip:

```bash
pip install hierarchical-docs-mcp
```

### Method 2: Install from Source

For the latest development version:

```bash
# Clone the repository
git clone https://github.com/esola-thomas/Markdown-MCP
cd Markdown-MCP

# Install in development mode
pip install -e .
```

## Verify Installation

After installation, verify it works:

```bash
hierarchical-docs-mcp --version
```

You should see the version number displayed.

## Next Steps

Now that you've installed the application, check out:

- [Configuration Guide](../configuration.md) - Learn how to configure the application
- [Quick Start Tutorial](#) - Get started with your first project
- [API Authentication](../../api/authentication.md) - Secure your API access

## Troubleshooting

### Common Issues

**Permission denied error**
```bash
# Use --user flag to install in user directory
pip install --user hierarchical-docs-mcp
```

**Python version too old**
```bash
# Check your Python version
python --version

# Upgrade Python if needed
# Visit python.org for instructions
```

## Getting Help

If you encounter issues:

- Check the [troubleshooting guide](#)
- Search existing [GitHub issues](https://github.com/esola-thomas/Markdown-MCP/issues)
- Join our [community forum](#)
