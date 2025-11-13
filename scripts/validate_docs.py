#!/usr/bin/env python3
"""
Documentation Validation Script

Validates markdown documentation files against project standards:
- YAML frontmatter validation
- Markdown syntax checks
- Link validation
- Line length limits
- Code block language tags
- Content quality checks

Usage:
    python scripts/validate_docs.py [paths...] [options]

Examples:
    python scripts/validate_docs.py docs/
    python scripts/validate_docs.py docs/guides/getting-started.md
    python scripts/validate_docs.py docs/ --fix
    python scripts/validate_docs.py docs/ --report=validation-report.md
"""

import argparse
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)


class Severity(Enum):
    """Issue severity levels."""

    CRITICAL = "critical"  # Must fix
    WARNING = "warning"  # Should fix
    INFO = "info"  # Optional


@dataclass
class ValidationIssue:
    """Represents a validation issue found in documentation."""

    severity: Severity
    file_path: str
    line_number: int | None
    issue: str
    current: str | None = None
    fix: str | None = None
    suggestion: str | None = None

    def __str__(self) -> str:
        """Format issue as human-readable string."""
        emoji = {Severity.CRITICAL: "❌", Severity.WARNING: "⚠️", Severity.INFO: "ℹ️"}

        result = f"{emoji[self.severity]} {self.severity.value.upper()}: {self.issue}\n"
        result += f"   Location: {self.file_path}:{self.line_number or 0}\n"

        if self.current:
            result += f"   Current: {self.current[:80]}\n"
        if self.fix:
            result += f"   Fix: {self.fix[:80]}\n"
        if self.suggestion:
            result += f"   Suggestion: {self.suggestion}\n"

        return result


@dataclass
class ValidationResult:
    """Results of validating a documentation file."""

    file_path: str
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.CRITICAL)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.INFO)

    @property
    def has_critical(self) -> bool:
        return self.critical_count > 0

    @property
    def passed(self) -> bool:
        return self.critical_count == 0


class DocumentValidator:
    """Validates markdown documentation files."""

    REQUIRED_FRONTMATTER = ["title", "category", "tags", "order"]
    VALID_CATEGORIES = [
        "Guides",
        "API Reference",
        "Architecture",
        "Configuration",
        "Security",
        "Development",
        "Tutorials",
    ]
    MAX_LINE_LENGTH = 100

    def __init__(self, docs_root: Path):
        self.docs_root = docs_root
        self.results: list[ValidationResult] = []

    def validate_file(self, file_path: Path) -> ValidationResult:
        """Validate a single markdown file."""
        result = ValidationResult(file_path=str(file_path))

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                lines = content.splitlines()
        except Exception as e:
            result.issues.append(
                ValidationIssue(
                    severity=Severity.CRITICAL,
                    file_path=str(file_path),
                    line_number=None,
                    issue=f"Failed to read file: {e}",
                )
            )
            return result

        # Run validation checks
        self._validate_frontmatter(file_path, content, result)
        self._validate_headers(file_path, lines, result)
        self._validate_code_blocks(file_path, lines, result)
        self._validate_line_length(file_path, lines, result)
        self._validate_links(file_path, lines, result)
        self._validate_lists(file_path, lines, result)
        self._validate_content_structure(file_path, content, result)

        self.results.append(result)
        return result

    def _validate_frontmatter(
        self, file_path: Path, content: str, result: ValidationResult
    ) -> None:
        """Validate YAML frontmatter."""
        if not content.startswith("---"):
            result.issues.append(
                ValidationIssue(
                    severity=Severity.CRITICAL,
                    file_path=str(file_path),
                    line_number=1,
                    issue="Missing YAML frontmatter",
                    fix="Add YAML frontmatter at the beginning of the file",
                )
            )
            return

        parts = content.split("---", 2)
        if len(parts) < 3:
            result.issues.append(
                ValidationIssue(
                    severity=Severity.CRITICAL,
                    file_path=str(file_path),
                    line_number=1,
                    issue="Incomplete YAML frontmatter (missing closing ---)",
                    fix="Add closing --- after frontmatter",
                )
            )
            return

        frontmatter_text = parts[1]

        # Try to parse YAML
        try:
            frontmatter = yaml.safe_load(frontmatter_text)
        except yaml.YAMLError as e:
            result.issues.append(
                ValidationIssue(
                    severity=Severity.CRITICAL,
                    file_path=str(file_path),
                    line_number=self._get_yaml_error_line(str(e)),
                    issue=f"Invalid YAML syntax: {e}",
                    suggestion="Check for proper quoting, indentation, and syntax",
                )
            )
            return

        if not isinstance(frontmatter, dict):
            result.issues.append(
                ValidationIssue(
                    severity=Severity.CRITICAL,
                    file_path=str(file_path),
                    line_number=2,
                    issue="Frontmatter must be a dictionary",
                    fix="Use key: value pairs in frontmatter",
                )
            )
            return

        # Check required fields
        for field_name in self.REQUIRED_FRONTMATTER:
            if field_name not in frontmatter:
                result.issues.append(
                    ValidationIssue(
                        severity=Severity.CRITICAL,
                        file_path=str(file_path),
                        line_number=None,
                        issue=f"Missing required frontmatter field: {field_name}",
                        fix=f"Add '{field_name}:' to frontmatter",
                    )
                )

        # Validate field types and values
        if "title" in frontmatter:
            if not isinstance(frontmatter["title"], str):
                result.issues.append(
                    ValidationIssue(
                        severity=Severity.CRITICAL,
                        file_path=str(file_path),
                        line_number=None,
                        issue="'title' must be a string",
                        current=str(frontmatter["title"]),
                        fix='title: "Your Title Here"',
                    )
                )

        if "category" in frontmatter:
            if not isinstance(frontmatter["category"], str):
                result.issues.append(
                    ValidationIssue(
                        severity=Severity.WARNING,
                        file_path=str(file_path),
                        line_number=None,
                        issue="'category' should be a string",
                        current=str(frontmatter["category"]),
                    )
                )
            elif frontmatter["category"] not in self.VALID_CATEGORIES:
                result.issues.append(
                    ValidationIssue(
                        severity=Severity.INFO,
                        file_path=str(file_path),
                        line_number=None,
                        issue=f"Unusual category: {frontmatter['category']}",
                        suggestion=f"Common categories: {', '.join(self.VALID_CATEGORIES)}",
                    )
                )

        if "tags" in frontmatter:
            if not isinstance(frontmatter["tags"], list):
                result.issues.append(
                    ValidationIssue(
                        severity=Severity.CRITICAL,
                        file_path=str(file_path),
                        line_number=None,
                        issue="'tags' must be an array",
                        current=str(frontmatter["tags"]),
                        fix='tags: ["tag1", "tag2"]',
                    )
                )
            elif len(frontmatter["tags"]) == 0:
                result.issues.append(
                    ValidationIssue(
                        severity=Severity.WARNING,
                        file_path=str(file_path),
                        line_number=None,
                        issue="'tags' array is empty",
                        suggestion="Add relevant tags for searchability",
                    )
                )

        if "order" in frontmatter:
            if not isinstance(frontmatter["order"], int):
                result.issues.append(
                    ValidationIssue(
                        severity=Severity.CRITICAL,
                        file_path=str(file_path),
                        line_number=None,
                        issue="'order' must be an integer",
                        current=str(frontmatter["order"]),
                        fix="order: 1",
                    )
                )

    def _validate_headers(
        self, file_path: Path, lines: list[str], result: ValidationResult
    ) -> None:
        """Validate markdown headers."""
        headers = []
        h1_count = 0
        in_frontmatter = False
        frontmatter_closed = False
        in_code_block = False

        for i, line in enumerate(lines, 1):
            # Track code blocks
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                continue

            # Track frontmatter
            if line.strip() == "---":
                if not in_frontmatter and not frontmatter_closed:
                    in_frontmatter = True
                    continue
                elif in_frontmatter:
                    in_frontmatter = False
                    frontmatter_closed = True
                    continue

            if in_frontmatter:
                continue

            if line.startswith("#"):
                # Check for space after #
                if not re.match(r"^#+\s", line):
                    result.issues.append(
                        ValidationIssue(
                            severity=Severity.WARNING,
                            file_path=str(file_path),
                            line_number=i,
                            issue="Missing space after # in header",
                            current=line,
                            fix=line.replace("#", "# ", 1),
                        )
                    )

                level = len(line) - len(line.lstrip("#"))
                level = min(level, line.index(" ") if " " in line else level)
                headers.append((i, level, line))

                if level == 1:
                    h1_count += 1

        # Check H1 count
        if h1_count == 0:
            result.issues.append(
                ValidationIssue(
                    severity=Severity.WARNING,
                    file_path=str(file_path),
                    line_number=None,
                    issue="No H1 header found",
                    suggestion="Add a main title with # Header",
                )
            )
        elif h1_count > 1:
            result.issues.append(
                ValidationIssue(
                    severity=Severity.CRITICAL,
                    file_path=str(file_path),
                    line_number=None,
                    issue=f"Multiple H1 headers found ({h1_count})",
                    fix="Use only one H1 header per document",
                )
            )

        # Check header hierarchy
        for i in range(1, len(headers)):
            prev_line, prev_level, prev_text = headers[i - 1]
            curr_line, curr_level, curr_text = headers[i]

            if curr_level > prev_level + 1:
                result.issues.append(
                    ValidationIssue(
                        severity=Severity.CRITICAL,
                        file_path=str(file_path),
                        line_number=curr_line,
                        issue=f"Skipped header level (H{prev_level} -> H{curr_level})",
                        current=curr_text,
                        fix=f"Use H{prev_level + 1} instead",
                    )
                )

    def _validate_code_blocks(
        self, file_path: Path, lines: list[str], result: ValidationResult
    ) -> None:
        """Validate code blocks have language specifiers."""
        in_code_block = False

        for i, line in enumerate(lines, 1):
            if line.strip().startswith("```"):
                if not in_code_block:
                    # Opening code block
                    lang = line.strip()[3:].strip()
                    if not lang:
                        result.issues.append(
                            ValidationIssue(
                                severity=Severity.CRITICAL,
                                file_path=str(file_path),
                                line_number=i,
                                issue="Code block missing language specifier",
                                current=line,
                                fix="```python (or appropriate language)",
                            )
                        )
                    in_code_block = True
                else:
                    # Closing code block
                    in_code_block = False

    def _validate_line_length(
        self, file_path: Path, lines: list[str], result: ValidationResult
    ) -> None:
        """Validate line length limits."""
        in_code_block = False
        in_table = False

        for i, line in enumerate(lines, 1):
            # Skip code blocks
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                continue

            # Skip tables
            if "|" in line:
                in_table = True
            elif in_table and not line.strip():
                in_table = False

            if in_table:
                continue

            # Skip URLs
            if "http://" in line or "https://" in line:
                continue

            if len(line) > self.MAX_LINE_LENGTH:
                result.issues.append(
                    ValidationIssue(
                        severity=Severity.WARNING,
                        file_path=str(file_path),
                        line_number=i,
                        issue=f"Line exceeds {self.MAX_LINE_LENGTH} characters ({len(line)} chars)",
                        current=line[:80] + "...",
                        suggestion="Break line at logical point (punctuation, conjunction)",
                    )
                )

    def _validate_links(self, file_path: Path, lines: list[str], result: ValidationResult) -> None:
        """Validate internal and external links."""
        link_pattern = r"\[([^\]]+)\]\(([^\)]+)\)"

        for i, line in enumerate(lines, 1):
            for match in re.finditer(link_pattern, line):
                link_text = match.group(1)
                link_url = match.group(2)

                # Check for poor link text
                if link_text.lower() in ["here", "click here", "this", "link"]:
                    result.issues.append(
                        ValidationIssue(
                            severity=Severity.WARNING,
                            file_path=str(file_path),
                            line_number=i,
                            issue=f"Non-descriptive link text: '{link_text}'",
                            current=match.group(0),
                            suggestion="Use descriptive text that explains the destination",
                        )
                    )

                # Validate internal links
                if link_url.startswith("./") or link_url.startswith("../"):
                    # Extract path (remove anchor)
                    link_path = link_url.split("#")[0]

                    # Check for .md extension
                    if not link_path.endswith(".md") and not link_path.endswith("/"):
                        result.issues.append(
                            ValidationIssue(
                                severity=Severity.WARNING,
                                file_path=str(file_path),
                                line_number=i,
                                issue=f"Internal link missing .md extension: {link_path}",
                                current=link_url,
                                fix=link_url.replace(link_path, link_path + ".md"),
                            )
                        )

                    # Check if target exists
                    if link_path.endswith(".md"):
                        target_path = (file_path.parent / link_path).resolve()
                        if not target_path.exists():
                            result.issues.append(
                                ValidationIssue(
                                    severity=Severity.CRITICAL,
                                    file_path=str(file_path),
                                    line_number=i,
                                    issue=f"Broken internal link: {link_url}",
                                    current=match.group(0),
                                    suggestion=f"Target file does not exist: {target_path}",
                                )
                            )

                # Check for absolute paths
                elif link_url.startswith("/") and not link_url.startswith("//"):
                    result.issues.append(
                        ValidationIssue(
                            severity=Severity.WARNING,
                            file_path=str(file_path),
                            line_number=i,
                            issue=f"Absolute path used for internal link: {link_url}",
                            current=match.group(0),
                            suggestion="Use relative paths (./file.md or ../parent/file.md)",
                        )
                    )

    def _validate_lists(self, file_path: Path, lines: list[str], result: ValidationResult) -> None:
        """Validate list formatting."""
        in_code_block = False
        bullet_chars = set()

        for i, line in enumerate(lines, 1):
            # Track code blocks
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                continue

            # Check for unordered list items
            if re.match(r"^[\s]*[-*+]\s", line):
                # Extract bullet character
                bullet = re.match(r"^[\s]*([-*+])", line).group(1)
                bullet_chars.add(bullet)

                # Check indentation (should be multiple of 2)
                indent = len(line) - len(line.lstrip())
                if indent % 2 != 0:
                    result.issues.append(
                        ValidationIssue(
                            severity=Severity.WARNING,
                            file_path=str(file_path),
                            line_number=i,
                            issue=f"List item indentation should be multiple of 2 (found {indent})",
                            current=line,
                            suggestion="Use 2-space indentation for nested lists",
                        )
                    )

        # Check for inconsistent bullet characters
        if len(bullet_chars) > 1:
            result.issues.append(
                ValidationIssue(
                    severity=Severity.WARNING,
                    file_path=str(file_path),
                    line_number=None,
                    issue=f"Inconsistent bullet characters: {bullet_chars}",
                    suggestion="Use consistent bullet character throughout (prefer '-')",
                )
            )

    def _validate_content_structure(
        self, file_path: Path, content: str, result: ValidationResult
    ) -> None:
        """Validate overall content structure."""
        lines = content.splitlines()

        # Skip frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content_without_frontmatter = parts[2]
                lines = content_without_frontmatter.splitlines()

        # Count sections (H2 headers)
        section_count = sum(1 for line in lines if line.startswith("## "))

        # Check for table of contents
        has_toc = any("table of contents" in line.lower() for line in lines)

        if section_count > 3 and not has_toc:
            result.issues.append(
                ValidationIssue(
                    severity=Severity.INFO,
                    file_path=str(file_path),
                    line_number=None,
                    issue=f"Document has {section_count} sections but no table of contents",
                    suggestion="Add table of contents for better navigation",
                )
            )

        # Check for examples section in guides/tutorials
        if "guide" in str(file_path).lower() or "tutorial" in str(file_path).lower():
            has_examples = any("example" in line.lower() for line in lines)
            if not has_examples:
                result.issues.append(
                    ValidationIssue(
                        severity=Severity.INFO,
                        file_path=str(file_path),
                        line_number=None,
                        issue="Guide/tutorial missing examples section",
                        suggestion="Add practical examples to help readers",
                    )
                )

    @staticmethod
    def _get_yaml_error_line(error_msg: str) -> int | None:
        """Extract line number from YAML error message."""
        match = re.search(r"line (\d+)", error_msg)
        return int(match.group(1)) if match else None

    def generate_report(self, output_path: Path | None = None) -> str:
        """Generate validation report."""
        report_lines = ["# Documentation Validation Report\n"]

        total_critical = sum(r.critical_count for r in self.results)
        total_warning = sum(r.warning_count for r in self.results)
        total_info = sum(r.info_count for r in self.results)
        total_issues = total_critical + total_warning + total_info

        files_with_issues = sum(1 for r in self.results if r.issues)
        files_passed = sum(1 for r in self.results if r.passed)

        # Summary
        report_lines.append("## Summary\n")
        report_lines.append(f"**Total Files:** {len(self.results)}")
        report_lines.append(f"**Files Passed:** {files_passed} ✅")
        report_lines.append(f"**Files with Issues:** {files_with_issues}")
        report_lines.append(f"**Total Issues:** {total_issues}")
        report_lines.append(f"- Critical: {total_critical} ❌")
        report_lines.append(f"- Warnings: {total_warning} ⚠️")
        report_lines.append(f"- Info: {total_info} ℹ️\n")

        # Results by severity
        if total_critical > 0:
            report_lines.append("## Critical Issues (Must Fix)\n")
            for result in self.results:
                critical = [i for i in result.issues if i.severity == Severity.CRITICAL]
                if critical:
                    report_lines.append(f"### {result.file_path}\n")
                    for issue in critical:
                        report_lines.append(f"**Line {issue.line_number or 'N/A'}:** {issue.issue}")
                        if issue.current:
                            report_lines.append(f"```\nCurrent: {issue.current}\n```")
                        if issue.fix:
                            report_lines.append(f"```\nFix: {issue.fix}\n```")
                        report_lines.append("")

        if total_warning > 0:
            report_lines.append("## Warnings (Should Fix)\n")
            for result in self.results:
                warnings = [i for i in result.issues if i.severity == Severity.WARNING]
                if warnings:
                    report_lines.append(f"### {result.file_path}\n")
                    for issue in warnings[:5]:  # Limit to 5 per file
                        report_lines.append(f"**Line {issue.line_number or 'N/A'}:** {issue.issue}")
                        if issue.suggestion:
                            report_lines.append(f"*Suggestion: {issue.suggestion}*")
                        report_lines.append("")

        report = "\n".join(report_lines)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report)

        return report


def main():
    """Main entry point for the validation script."""
    parser = argparse.ArgumentParser(
        description="Validate markdown documentation against project standards"
    )
    parser.add_argument(
        "paths", nargs="+", help="Paths to markdown files or directories to validate"
    )
    parser.add_argument("--report", help="Output detailed report to file")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to auto-fix issues where possible (not implemented yet)",
    )
    parser.add_argument("--no-warnings", action="store_true", help="Only report critical issues")

    args = parser.parse_args()

    # Collect all markdown files to validate
    files_to_validate = []
    for path_str in args.paths:
        path = Path(path_str)
        if not path.exists():
            print(f"Error: Path does not exist: {path}", file=sys.stderr)
            continue

        if path.is_file() and path.suffix == ".md":
            files_to_validate.append(path)
        elif path.is_dir():
            files_to_validate.extend(path.rglob("*.md"))

    if not files_to_validate:
        print("No markdown files found to validate", file=sys.stderr)
        return 1

    # Validate files
    validator = DocumentValidator(docs_root=Path.cwd())

    print(f"Validating {len(files_to_validate)} markdown files...\n")

    for file_path in sorted(files_to_validate):
        result = validator.validate_file(file_path)

        if result.passed:
            print(f"✅ {file_path}")
        else:
            print(
                f"❌ {file_path} ({result.critical_count} critical, "
                f"{result.warning_count} warnings, {result.info_count} info)"
            )

            if not args.no_warnings:
                for issue in result.issues:
                    print(f"   {issue}")

    # Generate report
    print("\n" + "=" * 80)
    report = validator.generate_report(output_path=Path(args.report) if args.report else None)
    print(report)

    # Exit with error if critical issues found
    has_critical = any(r.has_critical for r in validator.results)
    if has_critical:
        print("\n❌ Validation failed: Critical issues must be fixed")
        return 1
    else:
        print("\n✅ Validation passed: No critical issues found")
        return 0


if __name__ == "__main__":
    sys.exit(main())
