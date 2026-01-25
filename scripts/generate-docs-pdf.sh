#!/bin/bash
# Generate PDF documentation release with optional confidentiality markings
# Requires: pandoc, xelatex (texlive-xetex)
#
# Usage: ./scripts/generate-docs-pdf.sh [version] [--confidential]
# Example: ./scripts/generate-docs-pdf.sh 2.0.0
# Example: ./scripts/generate-docs-pdf.sh 2.0.0 --confidential

set -e

PROJECT_NAME="your-docs-mcp"
OUTPUT_DIR="releases"
TIMESTAMP=$(date +%Y-%m-%d)
YEAR=$(date +%Y)

# Parse arguments
VERSION=""
CONFIDENTIAL=false

for arg in "$@"; do
    case $arg in
        --confidential)
            CONFIDENTIAL=true
            shift
            ;;
        *)
            if [[ -z "$VERSION" ]]; then
                VERSION="$arg"
            fi
            ;;
    esac
done

VERSION="${VERSION:-$(date +%Y.%m.%d)}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

echo -e "${BLUE}Generating ${PROJECT_NAME} Documentation v${VERSION}${NC}"
if [[ "$CONFIDENTIAL" == "true" ]]; then
    echo -e "${RED}Confidentiality markings: ENABLED${NC}"
else
    echo -e "${GREEN}Confidentiality markings: disabled (use --confidential to enable)${NC}"
fi

# Check for pandoc
if ! command -v pandoc &> /dev/null; then
    echo -e "${RED}Error: pandoc is required. Install with: sudo apt install pandoc${NC}"
    exit 1
fi

# Check for xelatex (preferred PDF engine)
PDF_ENGINE="xelatex"
if ! command -v xelatex &> /dev/null; then
    echo -e "${YELLOW}Warning: xelatex not found. Trying pdflatex...${NC}"
    if command -v pdflatex &> /dev/null; then
        PDF_ENGINE="pdflatex"
    else
        echo -e "${YELLOW}Warning: No LaTeX engine found. PDF generation may fail.${NC}"
        echo -e "${YELLOW}Install with: sudo apt install texlive-xetex${NC}"
    fi
fi

# Check for Python and Pillow (for ASCII art conversion)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Try multiple Python locations
PYTHON=""
for py in "$PROJECT_ROOT/venv/bin/python" "$PROJECT_ROOT/.venv/bin/python" "python3" "python"; do
    if command -v "$py" &> /dev/null; then
        PYTHON="$py"
        break
    fi
done

ASCII2IMG="${SCRIPT_DIR}/ascii2image.py"
CONVERT_ASCII=false

if [[ -n "$PYTHON" ]] && [[ -f "$ASCII2IMG" ]]; then
    if "$PYTHON" -c "from PIL import Image" 2>/dev/null; then
        CONVERT_ASCII=true
        echo -e "${GREEN}ASCII art conversion: enabled${NC}"
    else
        echo -e "${YELLOW}Warning: Pillow not installed. ASCII diagrams may not render correctly.${NC}"
        echo -e "${YELLOW}Install with: pip install Pillow${NC}"
    fi
else
    echo -e "${YELLOW}Warning: ASCII art converter not available. Diagrams may not render correctly.${NC}"
fi

# Create output directory and temp workspace
mkdir -p "$OUTPUT_DIR"
WORK_DIR=$(mktemp -d)
IMG_DIR="$WORK_DIR/diagrams"
mkdir -p "$IMG_DIR"

# Cleanup function
cleanup() {
    rm -rf "$WORK_DIR" 2>/dev/null || true
}
trap cleanup EXIT

# Create combined markdown file with proper ordering
COMBINED_MD="$WORK_DIR/combined.md"
TITLE_PAGE="$WORK_DIR/title.md"
LATEX_HEADER="$WORK_DIR/header.tex"

# Generate LaTeX header based on confidentiality setting
if [[ "$CONFIDENTIAL" == "true" ]]; then
    # LaTeX header for confidentiality markings (headers, footers, watermarks)
    cat > "$LATEX_HEADER" << 'LATEX_EOF'
% Confidentiality headers and footers
\usepackage{fancyhdr}
\usepackage{lastpage}
\usepackage{xcolor}
\usepackage{draftwatermark}

% Watermark configuration
\SetWatermarkText{CONFIDENTIAL}
\SetWatermarkScale{0.5}
\SetWatermarkColor[gray]{0.9}
\SetWatermarkAngle{45}

% Page style with headers and footers
\pagestyle{fancy}
\fancyhf{}

% Header
\fancyhead[L]{\small\textcolor{red}{\textbf{PROJECT_NAME_PLACEHOLDER — CONFIDENTIAL \& PROPRIETARY}}}
\fancyhead[R]{\small\textit{vVERSION_PLACEHOLDER}}

% Footer
\fancyfoot[L]{\small\textcolor{gray}{© YEAR_PLACEHOLDER PROJECT_NAME_PLACEHOLDER All Rights Reserved.}}
\fancyfoot[C]{\small\textcolor{red}{\textbf{DO NOT DISTRIBUTE}}}
\fancyfoot[R]{\small Page \thepage\ of \pageref{LastPage}}

% Reduce header/footer rule visibility
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\footrulewidth}{0.4pt}

% Apply to plain pages (chapter starts, TOC)
\fancypagestyle{plain}{
  \fancyhf{}
  \fancyhead[L]{\small\textcolor{red}{\textbf{PROJECT_NAME_PLACEHOLDER — CONFIDENTIAL \& PROPRIETARY}}}
  \fancyhead[R]{\small\textit{vVERSION_PLACEHOLDER}}
  \fancyfoot[L]{\small\textcolor{gray}{© YEAR_PLACEHOLDER PROJECT_NAME_PLACEHOLDER All Rights Reserved.}}
  \fancyfoot[C]{\small\textcolor{red}{\textbf{DO NOT DISTRIBUTE}}}
  \fancyfoot[R]{\small Page \thepage\ of \pageref{LastPage}}
  \renewcommand{\headrulewidth}{0.4pt}
  \renewcommand{\footrulewidth}{0.4pt}
}
LATEX_EOF

    # Substitute placeholders in LaTeX header
    sed -i "s/PROJECT_NAME_PLACEHOLDER/${PROJECT_NAME}/g" "$LATEX_HEADER"
    sed -i "s/VERSION_PLACEHOLDER/${VERSION}/g" "$LATEX_HEADER"
    sed -i "s/YEAR_PLACEHOLDER/${YEAR}/g" "$LATEX_HEADER"

    # Title page with confidentiality notice
    cat > "$TITLE_PAGE" << EOF
---
title: "${PROJECT_NAME} Technical Documentation"
subtitle: "MCP Server for AI-Powered Documentation Navigation"
author: "${PROJECT_NAME} Contributors"
date: "${TIMESTAMP}"
version: "v${VERSION}"
---

\\begin{center}
\\vspace*{1cm}

{\\Huge\\textbf{CONFIDENTIAL}}

\\vspace{0.5cm}

{\\large\\textcolor{red}{PROPRIETARY \\& TRADE SECRET INFORMATION}}

\\vspace{1cm}

\\rule{\\textwidth}{0.4pt}

\\vspace{0.5cm}

{\\small
This document contains confidential and proprietary information belonging exclusively to \\textbf{${PROJECT_NAME}}

\\vspace{0.3cm}

\\textbf{NOTICE:} This material is protected by copyright and trade secret laws. Unauthorized reproduction, distribution, or disclosure of this document or any portion thereof is strictly prohibited and may result in severe civil and criminal penalties.

\\vspace{0.3cm}

This document is provided under Non-Disclosure Agreement (NDA) to authorized recipients only.

\\vspace{0.5cm}

\\textbf{Document Classification:} CONFIDENTIAL \\\\
\\textbf{Document Version:} v${VERSION} \\\\
\\textbf{Generated:} ${TIMESTAMP} \\\\
\\textbf{Owner:} ${PROJECT_NAME}

}

\\vspace{0.5cm}

\\rule{\\textwidth}{0.4pt}

\\vspace{1cm}

{\\footnotesize © ${YEAR} ${PROJECT_NAME} All rights reserved.}

\\end{center}

\\newpage

# Table of Contents

\\newpage

EOF
else
    # Simple header without confidentiality markings
    cat > "$LATEX_HEADER" << 'LATEX_EOF'
% Simple page style
\usepackage{fancyhdr}
\usepackage{lastpage}

\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\textit{PROJECT_NAME_PLACEHOLDER Documentation}}
\fancyhead[R]{\small\textit{vVERSION_PLACEHOLDER}}
\fancyfoot[C]{\small Page \thepage\ of \pageref{LastPage}}
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\footrulewidth}{0pt}

\fancypagestyle{plain}{
  \fancyhf{}
  \fancyhead[L]{\small\textit{PROJECT_NAME_PLACEHOLDER Documentation}}
  \fancyhead[R]{\small\textit{vVERSION_PLACEHOLDER}}
  \fancyfoot[C]{\small Page \thepage\ of \pageref{LastPage}}
  \renewcommand{\headrulewidth}{0.4pt}
  \renewcommand{\footrulewidth}{0pt}
}
LATEX_EOF

    sed -i "s/PROJECT_NAME_PLACEHOLDER/${PROJECT_NAME}/g" "$LATEX_HEADER"
    sed -i "s/VERSION_PLACEHOLDER/${VERSION}/g" "$LATEX_HEADER"

    # Simple title page
    cat > "$TITLE_PAGE" << EOF
---
title: "${PROJECT_NAME} Documentation"
subtitle: "MCP Server for AI-Powered Documentation Navigation"
author: "${PROJECT_NAME} Contributors"
date: "${TIMESTAMP}"
version: "v${VERSION}"
---

\\newpage

# Table of Contents

\\newpage

EOF
fi

cat "$TITLE_PAGE" > "$COMBINED_MD"

# Add documents in logical order
echo -e "${GREEN}Collecting documentation...${NC}"

# Function to add section with header (with ASCII art preprocessing)
add_section() {
    local file="$1"
    local title="$2"
    if [[ -f "$file" ]]; then
        echo "" >> "$COMBINED_MD"
        echo "# $title" >> "$COMBINED_MD"
        echo "" >> "$COMBINED_MD"
        
        # Preprocess ASCII art if enabled
        if [[ "$CONVERT_ASCII" == "true" ]]; then
            # Process file to convert ASCII art to images
            local processed_file="$WORK_DIR/$(basename "$file")"
            "$PYTHON" "$ASCII2IMG" "$file" "$processed_file" --img-dir "$IMG_DIR" 2>/dev/null || true
            if [[ -f "$processed_file" ]]; then
                # Remove YAML frontmatter, strip emojis, and add to combined
                sed '/^---$/,/^---$/d' "$processed_file" | \
                    sed 's/📚/[DOC]/g; s/🚀/[LAUNCH]/g; s/✅/[OK]/g; s/❌/[X]/g; s/⚠️/[WARN]/g; s/📋/[LIST]/g; s/✓/[v]/g; s/≤/<=/g' >> "$COMBINED_MD"
            else
                sed '/^---$/,/^---$/d' "$file" | \
                    sed 's/📚/[DOC]/g; s/🚀/[LAUNCH]/g; s/✅/[OK]/g; s/❌/[X]/g; s/⚠️/[WARN]/g; s/📋/[LIST]/g; s/✓/[v]/g; s/≤/<=/g' >> "$COMBINED_MD"
            fi
        else
            # Just remove YAML frontmatter and strip emojis
            sed '/^---$/,/^---$/d' "$file" | \
                sed 's/📚/[DOC]/g; s/🚀/[LAUNCH]/g; s/✅/[OK]/g; s/❌/[X]/g; s/⚠️/[WARN]/g; s/📋/[LIST]/g; s/✓/[v]/g; s/≤/<=/g' >> "$COMBINED_MD"
        fi
        
        echo "" >> "$COMBINED_MD"
        echo "\\newpage" >> "$COMBINED_MD"
        echo -e "  ${GREEN}Added:${NC} $title"
    else
        echo -e "  ${YELLOW}Skipped (not found):${NC} $file"
    fi
}

# Main README
add_section "README.md" "Overview"

# Architecture Section
echo "" >> "$COMBINED_MD"
echo "# PART I: Architecture" >> "$COMBINED_MD"
echo "" >> "$COMBINED_MD"
add_section "docs/architecture/overview.md" "Architecture Overview"
add_section "docs/architecture/mcp-protocol.md" "MCP Protocol Integration"
add_section "docs/architecture/vector-db.md" "Vector Database Integration"

# Guides Section
echo "" >> "$COMBINED_MD"
echo "# PART II: Guides" >> "$COMBINED_MD"
echo "" >> "$COMBINED_MD"
add_section "docs/guides/getting-started.md" "Getting Started"
add_section "docs/guides/quickstart/installation.md" "Installation Guide"
add_section "docs/guides/quickstart/configuration.md" "Configuration Guide"

# API Section
echo "" >> "$COMBINED_MD"
echo "# PART III: API Reference" >> "$COMBINED_MD"
echo "" >> "$COMBINED_MD"
add_section "docs/api/rest.md" "REST API Reference"

# Reference Section
echo "" >> "$COMBINED_MD"
echo "# PART IV: Reference" >> "$COMBINED_MD"
echo "" >> "$COMBINED_MD"
add_section "docs/reference/cli-commands.md" "CLI Commands Reference"

# Development Section
echo "" >> "$COMBINED_MD"
echo "# PART V: Development" >> "$COMBINED_MD"
echo "" >> "$COMBINED_MD"
add_section "docs/development/contributing.md" "Contributing Guide"
add_section "docs/development/testing.md" "Testing Guide"
add_section "docs/ci-cd-integration.md" "CI/CD Integration"
add_section "CHANGELOG.md" "Changelog"

# Add confidentiality footer if enabled
if [[ "$CONFIDENTIAL" == "true" ]]; then
    cat >> "$COMBINED_MD" << EOF

---

\\begin{center}
\\textbf{END OF DOCUMENT}

\\vspace{0.5cm}

{\\small This document contains confidential information of ${PROJECT_NAME}

Unauthorized use, reproduction, or distribution is strictly prohibited.}

\\vspace{0.5cm}

{\\footnotesize Document ID: ${PROJECT_NAME}-DOCS-v${VERSION}-$(date +%s | sha256sum | head -c 8)}
\\end{center}
EOF
fi

# Generate PDF
OUTPUT_FILE="$OUTPUT_DIR/${PROJECT_NAME}-docs-v${VERSION}.pdf"

echo -e "${GREEN}Generating PDF...${NC}"
if [[ "$CONVERT_ASCII" == "true" ]]; then
    echo -e "${BLUE}Converting ASCII diagrams to images...${NC}"
fi

# Build pandoc command
PANDOC_ARGS=(
    "$COMBINED_MD"
    -o "$OUTPUT_FILE"
    --toc
    --toc-depth=3
    --pdf-engine="$PDF_ENGINE"
    --resource-path="$WORK_DIR:$IMG_DIR"
    -H "$LATEX_HEADER"
    -V geometry:margin=1in
    -V documentclass=report
    -V fontsize=11pt
    -V colorlinks=true
    -V linkcolor=blue
    -V urlcolor=blue
    --highlight-style=tango
)

if [[ "$CONFIDENTIAL" == "true" ]]; then
    PANDOC_ARGS+=(-V geometry:top=1.2in -V geometry:bottom=1in)
fi

pandoc "${PANDOC_ARGS[@]}" || {
    echo -e "${RED}Error: PDF generation failed${NC}"
    echo "Check that texlive-xetex is installed: sudo apt install texlive-xetex texlive-latex-extra"
    exit 1
}

# Create manifest
if [[ "$CONFIDENTIAL" == "true" ]]; then
    cat > "$OUTPUT_DIR/manifest-v${VERSION}.json" << EOF
{
    "project": "${PROJECT_NAME}",
    "version": "${VERSION}",
    "generated": "${TIMESTAMP}",
    "classification": "CONFIDENTIAL",
    "distribution": "RESTRICTED - Authorized recipients only",
    "files": [
        "${PROJECT_NAME}-docs-v${VERSION}.pdf"
    ],
    "checksum": "$(sha256sum "$OUTPUT_FILE" 2>/dev/null | cut -d' ' -f1 || echo 'N/A')",
    "notice": "This document contains confidential and proprietary information. Unauthorized distribution is prohibited."
}
EOF
else
    cat > "$OUTPUT_DIR/manifest-v${VERSION}.json" << EOF
{
    "project": "${PROJECT_NAME}",
    "version": "${VERSION}",
    "generated": "${TIMESTAMP}",
    "files": [
        "${PROJECT_NAME}-docs-v${VERSION}.pdf"
    ],
    "checksum": "$(sha256sum "$OUTPUT_FILE" 2>/dev/null | cut -d' ' -f1 || echo 'N/A')"
}
EOF
fi

echo ""
echo -e "${GREEN}Done!${NC}"
echo "Output: $OUTPUT_FILE"
echo "Manifest: $OUTPUT_DIR/manifest-v${VERSION}.json"

if [[ "$CONFIDENTIAL" == "true" ]]; then
    echo ""
    echo -e "${RED}CONFIDENTIAL DOCUMENT GENERATED${NC}"
    echo "Classification: CONFIDENTIAL"
    echo "Distribution: Authorized recipients under NDA only"
fi
