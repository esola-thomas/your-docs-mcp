#!/bin/bash
# Generate PDF documentation release with optional confidentiality markings
# Dynamically discovers all markdown files in DOCS_ROOT
#
# Usage: ./scripts/generate-docs-pdf.sh [options] [version]
# Options:
#   --confidential         Enable confidentiality watermarks and notices
#   --title "Title"        Document title (default: PROJECT_NAME Documentation)
#   --subtitle "Subtitle"  Document subtitle
#   --author "Author"      Document author
#   --owner "Owner"        Copyright owner (for confidentiality notices)
#
# Examples:
#   ./scripts/generate-docs-pdf.sh 2.0.0
#   ./scripts/generate-docs-pdf.sh 2.0.0 --confidential --title "API Reference"
#   ./scripts/generate-docs-pdf.sh --title "My Docs" --author "My Company" 1.0.0
#
# Environment:
#   DOCS_ROOT - Documentation directory (default: ./docs)
#   PROJECT_NAME - Project name for the PDF (default: your-docs-mcp)

set -e

# Configuration from environment or defaults
DOCS_ROOT="${DOCS_ROOT:-./docs}"
PROJECT_NAME="${PROJECT_NAME:-your-docs-mcp}"
OUTPUT_DIR="releases"
TIMESTAMP=$(date +%Y-%m-%d)
YEAR=$(date +%Y)

# Defaults for customizable fields
DOC_TITLE=""
DOC_SUBTITLE="Complete Documentation Release"
DOC_AUTHOR=""
DOC_OWNER=""

# Parse arguments
VERSION=""
CONFIDENTIAL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --confidential)
            CONFIDENTIAL=true
            shift
            ;;
        --title)
            DOC_TITLE="$2"
            shift 2
            ;;
        --subtitle)
            DOC_SUBTITLE="$2"
            shift 2
            ;;
        --author)
            DOC_AUTHOR="$2"
            shift 2
            ;;
        --owner)
            DOC_OWNER="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [options] [version]"
            echo ""
            echo "Options:"
            echo "  --confidential         Enable confidentiality watermarks and notices"
            echo "  --title \"Title\"        Document title"
            echo "  --subtitle \"Subtitle\"  Document subtitle"
            echo "  --author \"Author\"      Document author"
            echo "  --owner \"Owner\"        Copyright owner"
            echo "  --help                 Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  DOCS_ROOT     Documentation directory (default: ./docs)"
            echo "  PROJECT_NAME  Project name (default: your-docs-mcp)"
            exit 0
            ;;
        -*)
            echo "Unknown option: $1"
            exit 1
            ;;
        *)
            if [[ -z "$VERSION" ]]; then
                VERSION="$1"
            fi
            shift
            ;;
    esac
done

VERSION="${VERSION:-$(date +%Y.%m.%d)}"

# Apply defaults where not specified
DOC_TITLE="${DOC_TITLE:-${PROJECT_NAME} Documentation}"
DOC_AUTHOR="${DOC_AUTHOR:-${PROJECT_NAME}}"
DOC_OWNER="${DOC_OWNER:-${PROJECT_NAME}}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

echo -e "${BLUE}Generating Documentation PDF${NC}"
echo -e "${BLUE}  Title: ${DOC_TITLE}${NC}"
echo -e "${BLUE}  Version: v${VERSION}${NC}"
echo -e "${BLUE}  Author: ${DOC_AUTHOR}${NC}"
echo -e "${BLUE}  Source: ${DOCS_ROOT}${NC}"
if [[ "$CONFIDENTIAL" == "true" ]]; then
    echo -e "${RED}  Confidentiality: ENABLED (Owner: ${DOC_OWNER})${NC}"
else
    echo -e "${GREEN}  Confidentiality: disabled${NC}"
fi

# Validate DOCS_ROOT exists
if [[ ! -d "$DOCS_ROOT" ]]; then
    echo -e "${RED}Error: DOCS_ROOT directory not found: ${DOCS_ROOT}${NC}"
    echo "Set DOCS_ROOT environment variable to your documentation directory"
    exit 1
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
    fi
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

# Create combined markdown file
COMBINED_MD="$WORK_DIR/combined.md"
TITLE_PAGE="$WORK_DIR/title.md"
LATEX_HEADER="$WORK_DIR/header.tex"

# Generate LaTeX header based on confidentiality setting
if [[ "$CONFIDENTIAL" == "true" ]]; then
    cat > "$LATEX_HEADER" << LATEX_EOF
\usepackage{fancyhdr}
\usepackage{lastpage}
\usepackage{xcolor}
\usepackage{draftwatermark}
\SetWatermarkText{CONFIDENTIAL}
\SetWatermarkScale{0.5}
\SetWatermarkColor[gray]{0.9}
\SetWatermarkAngle{45}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\textcolor{red}{\textbf{${DOC_OWNER} — CONFIDENTIAL}}}
\fancyhead[R]{\small\textit{v${VERSION}}}
\fancyfoot[L]{\small\textcolor{gray}{© ${YEAR} ${DOC_OWNER}}}
\fancyfoot[C]{\small\textcolor{red}{\textbf{DO NOT DISTRIBUTE}}}
\fancyfoot[R]{\small Page \thepage\ of \pageref{LastPage}}
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\footrulewidth}{0.4pt}
\fancypagestyle{plain}{\fancyhf{}\fancyhead[L]{\small\textcolor{red}{\textbf{${DOC_OWNER} — CONFIDENTIAL}}}\fancyhead[R]{\small\textit{v${VERSION}}}\fancyfoot[L]{\small\textcolor{gray}{© ${YEAR} ${DOC_OWNER}}}\fancyfoot[C]{\small\textcolor{red}{\textbf{DO NOT DISTRIBUTE}}}\fancyfoot[R]{\small Page \thepage\ of \pageref{LastPage}}\renewcommand{\headrulewidth}{0.4pt}\renewcommand{\footrulewidth}{0.4pt}}
LATEX_EOF
else
    cat > "$LATEX_HEADER" << LATEX_EOF
\usepackage{fancyhdr}
\usepackage{lastpage}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\textit{${DOC_TITLE}}}
\fancyhead[R]{\small\textit{v${VERSION}}}
\fancyfoot[C]{\small Page \thepage\ of \pageref{LastPage}}
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\footrulewidth}{0pt}
\fancypagestyle{plain}{\fancyhf{}\fancyhead[L]{\small\textit{${DOC_TITLE}}}\fancyhead[R]{\small\textit{v${VERSION}}}\fancyfoot[C]{\small Page \thepage\ of \pageref{LastPage}}\renewcommand{\headrulewidth}{0.4pt}\renewcommand{\footrulewidth}{0pt}}
LATEX_EOF
fi

# Title page
cat > "$TITLE_PAGE" << EOF
---
title: "${DOC_TITLE}"
subtitle: "${DOC_SUBTITLE}"
author: "${DOC_AUTHOR}"
date: "${TIMESTAMP}"
---

\newpage

EOF

cat "$TITLE_PAGE" > "$COMBINED_MD"

echo -e "${GREEN}Collecting documentation from ${DOCS_ROOT}...${NC}"

# Function to extract title from markdown file
get_title() {
    local file="$1"
    local title=$(sed -n '/^---$/,/^---$/p' "$file" 2>/dev/null | grep -E '^title:' | head -1 | sed 's/^title:[[:space:]]*//' | sed 's/^["'"'"']//' | sed 's/["'"'"']$//')
    if [[ -z "$title" ]]; then
        title=$(grep -m1 '^# ' "$file" 2>/dev/null | sed 's/^# //')
    fi
    if [[ -z "$title" ]]; then
        title=$(basename "$file" .md | sed 's/-/ /g' | sed 's/_/ /g')
    fi
    echo "$title"
}

# Function to remove YAML frontmatter (only the first --- block at start of file)
# This handles cases where --- appears later in the document as a separator
remove_frontmatter() {
    awk 'BEGIN{skip=0} NR==1 && /^---$/{skip=1; next} skip==1 && /^---$/{skip=0; next} !skip' "$@"
}

# Function to add a markdown file
add_file() {
    local file="$1"
    local title="$2"
    
    if [[ -f "$file" ]]; then
        echo "" >> "$COMBINED_MD"
        echo "## $title" >> "$COMBINED_MD"
        echo "" >> "$COMBINED_MD"
        
        if [[ "$CONVERT_ASCII" == "true" ]]; then
            # Create unique filename using relative path to avoid overwrites
            # e.g., architecture/overview.md -> architecture_overview.md
            local rel_path="${file#$DOCS_ROOT/}"
            local unique_name=$(echo "$rel_path" | sed 's|/|_|g' | sed 's/[^a-zA-Z0-9._-]/_/g')
            local processed_file="$WORK_DIR/$unique_name"
            "$PYTHON" "$ASCII2IMG" "$file" "$processed_file" --img-dir "$IMG_DIR" 2>/dev/null || cp "$file" "$processed_file"
            remove_frontmatter "$processed_file" | sed 's/📚/[DOC]/g; s/🚀/[LAUNCH]/g; s/✅/[OK]/g; s/❌/[X]/g; s/⚠️/[WARN]/g; s/📋/[LIST]/g; s/✓/[v]/g; s/🔧/[TOOL]/g; s/📦/[PKG]/g; s/🌐/[WEB]/g; s/💡/[IDEA]/g; s/⭐/[STAR]/g; s/🎯/[TARGET]/g; s/🔍/[SEARCH]/g; s/📝/[NOTE]/g; s/🛡️/[SECURE]/g; s/⚡/[FAST]/g; s/🔑/[KEY]/g; s/📊/[CHART]/g; s/🔄/[REFRESH]/g; s/➡️/->/g; s/⬅️/<-/g; s/↔️/<->/g; s/🔗/[LINK]/g' >> "$COMBINED_MD"
        else
            remove_frontmatter "$file" | sed 's/📚/[DOC]/g; s/🚀/[LAUNCH]/g; s/✅/[OK]/g; s/❌/[X]/g; s/⚠️/[WARN]/g; s/📋/[LIST]/g; s/✓/[v]/g; s/🔧/[TOOL]/g; s/📦/[PKG]/g; s/🌐/[WEB]/g; s/💡/[IDEA]/g; s/⭐/[STAR]/g; s/🎯/[TARGET]/g; s/🔍/[SEARCH]/g; s/📝/[NOTE]/g; s/🛡️/[SECURE]/g; s/⚡/[FAST]/g; s/🔑/[KEY]/g; s/📊/[CHART]/g; s/🔄/[REFRESH]/g; s/➡️/->/g; s/⬅️/<-/g; s/↔️/<->/g; s/🔗/[LINK]/g' >> "$COMBINED_MD"
        fi
        
        echo "" >> "$COMBINED_MD"
        echo "\newpage" >> "$COMBINED_MD"
        echo -e "  ${GREEN}Added:${NC} $title"
        return 0
    fi
    return 1
}

# Count total markdown files
TOTAL_FILES=$(find "$DOCS_ROOT" -name "*.md" -type f | wc -l)
echo -e "${BLUE}Found ${TOTAL_FILES} markdown files${NC}"

FILE_COUNT=0

# Process README at root first
if [[ -f "$DOCS_ROOT/README.md" ]]; then
    title=$(get_title "$DOCS_ROOT/README.md")
    add_file "$DOCS_ROOT/README.md" "$title"
    ((++FILE_COUNT))
fi

# Function to process a directory recursively
# Strategy: Process in hierarchical order: README first, then files, then subdirectories
process_directory() {
    local dir="$1"
    local depth="$2"
    local dir_name=$(basename "$dir")
    
    # Discover all markdown files in current directory (excluding README)
    local files=()
    while IFS= read -r -d '' file; do
        files+=("$file")
    done < <(find "$dir" -maxdepth 1 -name "*.md" -type f ! -name "README.md" -print0 2>/dev/null | sort -z)
    
    # Discover all subdirectories
    local subdirs=()
    while IFS= read -r -d '' subdir; do
        subdirs+=("$subdir")
    done < <(find "$dir" -maxdepth 1 -mindepth 1 -type d -print0 2>/dev/null | sort -z)
    
    # Add section header for non-root directories with content
    if [[ "$dir" != "$DOCS_ROOT" ]] && { [[ ${#files[@]} -gt 0 ]] || [[ ${#subdirs[@]} -gt 0 ]]; }; then
        local section_title=$(echo "$dir_name" | sed 's/-/ /g' | sed 's/_/ /g' | sed 's/\b./\u&/g')
        echo "" >> "$COMBINED_MD"
        echo "# $section_title" >> "$COMBINED_MD"
        echo "" >> "$COMBINED_MD"
        echo -e "${BLUE}Section:${NC} $section_title"
    fi
    
    # Process README first (overview/introduction for this section)
    if [[ -f "$dir/README.md" ]] && [[ "$dir" != "$DOCS_ROOT" ]]; then
        title=$(get_title "$dir/README.md")
        add_file "$dir/README.md" "$title"
        ((++FILE_COUNT))
    fi
    
    # Process all other markdown files in alphabetical order
    for file in "${files[@]}"; do
        title=$(get_title "$file")
        add_file "$file" "$title"
        ((++FILE_COUNT))
    done
    
    # Recursively process subdirectories (maintains hierarchy)
    for subdir in "${subdirs[@]}"; do
        process_directory "$subdir" $((depth + 1))
    done
}

# Process the documentation directory
process_directory "$DOCS_ROOT" 0

echo -e "${GREEN}Processed ${FILE_COUNT} files${NC}"

# Generate output filename from title or project name
OUTPUT_NAME=$(echo "$DOC_TITLE" | sed 's/[^a-zA-Z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//' | sed 's/-$//' | tr '[:upper:]' '[:lower:]')
OUTPUT_NAME="${OUTPUT_NAME:-${PROJECT_NAME}-docs}"
OUTPUT_FILE="$OUTPUT_DIR/${OUTPUT_NAME}-v${VERSION}.pdf"

echo -e "${GREEN}Generating PDF...${NC}"

# Use xelatex for better Unicode support, fallback gracefully
if [[ "$PDF_ENGINE" == "xelatex" ]]; then
    FONT_SETTINGS=(
        -V mainfont="DejaVu Sans"
        -V sansfont="DejaVu Sans"
        -V monofont="DejaVu Sans Mono"
    )
else
    FONT_SETTINGS=()
fi

PANDOC_ARGS=(
    "$COMBINED_MD"
    -o "$OUTPUT_FILE"
    --toc
    --toc-depth=3
    --pdf-engine="$PDF_ENGINE"
    --resource-path="$WORK_DIR:$IMG_DIR:$DOCS_ROOT"
    -H "$LATEX_HEADER"
    --metadata "title=${DOC_TITLE}"
    --metadata "subtitle=${DOC_SUBTITLE}"
    --metadata "author=${DOC_AUTHOR}"
    -V "subtitle=${DOC_SUBTITLE}"
    "${FONT_SETTINGS[@]}"
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

pandoc "${PANDOC_ARGS[@]}" 2>&1 | tee "$WORK_DIR/pandoc.log" || {
    echo -e "${RED}Error: PDF generation failed${NC}"
    echo -e "${YELLOW}Pandoc log:${NC}"
    cat "$WORK_DIR/pandoc.log"
    exit 1
}

# Create manifest
MANIFEST_FILE="$OUTPUT_DIR/manifest-${OUTPUT_NAME}-v${VERSION}.json"
cat > "$MANIFEST_FILE" << EOF
{
    "title": "${DOC_TITLE}",
    "subtitle": "${DOC_SUBTITLE}",
    "author": "${DOC_AUTHOR}",
    "owner": "${DOC_OWNER}",
    "version": "${VERSION}",
    "generated": "${TIMESTAMP}",
    "confidential": ${CONFIDENTIAL},
    "source": "${DOCS_ROOT}",
    "documents_included": ${FILE_COUNT},
    "files": ["$(basename "$OUTPUT_FILE")"],
    "checksum": "$(sha256sum "$OUTPUT_FILE" 2>/dev/null | cut -d' ' -f1 || echo 'N/A')"
}
EOF

echo ""
echo -e "${GREEN}Done!${NC}"
echo "Output: $OUTPUT_FILE"
echo "Manifest: $MANIFEST_FILE"
echo "Documents included: ${FILE_COUNT}"
