<!--
SYNC IMPACT REPORT - Constitution v1.0.0
===========================================
Version Change: TEMPLATE → 1.0.0
Rationale: Initial constitution establishment for Hierarchical Documentation MCP Server project

Modified Principles:
- Added I. Library-First Architecture
- Added II. Protocol Compliance
- Added III. Test-First Development (NON-NEGOTIABLE)
- Added IV. Security-By-Design
- Added V. Performance & Observability

Added Sections:
- Core Principles (5 principles defined)
- Quality Standards
- Development Workflow
- Governance

Templates Status:
✅ plan-template.md - Constitution Check section aligns with principles
✅ spec-template.md - User scenarios and requirements align with test-first approach
✅ tasks-template.md - Task categorization supports test-driven workflow
✅ .github/copilot-instructions.md - Will be updated with constitution reference

Follow-up TODOs:
- Update .github/copilot-instructions.md to reference constitution
- Add constitution compliance checks to CI/CD pipeline
- Create constitution.md reference in CONTRIBUTING.md

Commit Message: docs: establish project constitution v1.0.0 (initial principles + governance)
===========================================
-->

# Hierarchical Documentation MCP Server Constitution

## Core Principles

### I. Library-First Architecture

Every feature MUST be implemented as a standalone, self-contained library component. Libraries MUST be independently testable and have clear, single purposes. Organizational-only libraries (libraries created solely for grouping code) are prohibited.

**Rationale**: Clear separation of concerns enables independent testing, easier maintenance, and modular evolution. The MCP server is structured with isolated handlers/, models/, services/, and security/ modules that can be tested and evolved independently.

**Enforcement**: Code reviews MUST verify that new modules have clear purposes documented in their docstrings and that dependencies between modules are minimal and justified.

### II. Protocol Compliance

All MCP (Model Context Protocol) implementations MUST strictly follow the official MCP specification. Server MUST implement stdio transport for local use and support resource/tool contracts exactly as specified. Deviations from protocol standards are prohibited without explicit justification and documentation.

**Rationale**: Protocol compliance ensures interoperability with Claude Desktop, VS Code/GitHub Copilot, and other MCP-compatible AI assistants. Non-compliant implementations break the ecosystem.

**Enforcement**: Contract tests MUST validate MCP protocol compliance for every resource and tool. Integration tests MUST verify cross-platform compatibility (Claude Desktop and VS Code).

### III. Test-First Development (NON-NEGOTIABLE)

Test-Driven Development is mandatory. The workflow is: Write tests → Get user approval → Verify tests fail → Implement feature → Verify tests pass. Red-Green-Refactor cycle MUST be strictly enforced.

**Rationale**: TDD ensures testable design, prevents regression, and documents expected behavior. This project achieved 95%+ test coverage through disciplined TDD, catching edge cases before production.

**Enforcement**: Pull requests without corresponding tests MUST be rejected. Tests MUST fail before implementation (proof required in PR description). Minimum test coverage: 80% overall, with 95%+ target for new features.

### IV. Security-By-Design

Security validation MUST be implemented at system boundaries. All file paths MUST be validated to prevent directory traversal. All user inputs MUST be sanitized. Audit logging MUST track all security-relevant operations.

**Rationale**: Documentation servers process untrusted paths and queries. A single directory traversal vulnerability could expose sensitive files. Security cannot be retrofitted—it must be built-in from the start.

**Enforcement**: The security/ module MUST be consulted for all file operations and user input processing. Integration tests MUST include attack pattern validation (directory traversal, injection attempts). Security reviews are required for all PR merges.

### V. Performance & Observability

Performance goals MUST be defined and measured. Text-based I/O MUST be used for debuggability. Structured logging MUST capture all operations with appropriate severity levels. Performance targets: <2s retrieval (1GB docs), <3s search (5000 docs), <500ms navigation.

**Rationale**: Documentation servers must be responsive to maintain AI assistant workflow. Text I/O and structured logging enable debugging production issues without additional tooling. Performance regressions are easier to prevent than to fix.

**Enforcement**: Performance benchmarks MUST be run for every release. Logging MUST use docs_mcp.utils.logger for consistency. Performance degradation >20% requires justification and approval.

## Quality Standards

**Test Coverage**: Minimum 80% overall, target 95%+ for new features. Current project coverage: 94.90%.

**Test Structure**: Three-tier testing MUST be maintained:
- Contract tests: MCP protocol compliance, API contracts
- Integration tests: Cross-module workflows, security validation, platform compatibility
- Unit tests: Individual module behavior, edge cases, error paths

**Code Quality**: Python code MUST pass ruff linting with zero violations. Type hints MUST be used for all public interfaces. Docstrings MUST document all public classes, methods, and functions.

**Dependency Management**: Dependencies MUST have minimum versions specified. New dependencies require justification (why existing alternatives are insufficient). Transitive dependency vulnerabilities MUST be addressed within 7 days of disclosure.

## Development Workflow

**Feature Development**: All features MUST follow the spec-plan-tasks workflow:
1. Create feature specification in specs/###-feature-name/spec.md
2. Generate implementation plan with constitution compliance check
3. Generate tasks.md after design approval
4. Implement per tasks, marking completion incrementally

**Constitution Compliance**: Every implementation plan MUST include "Constitution Check" section. Plans that violate principles MUST document justification in "Complexity Tracking" section. Unjustified violations block progression to implementation.

**Branch Strategy**: Feature branches MUST be named ###-feature-name matching spec directory. Branches MUST be created from main and merged back via pull request after review.

**Review Requirements**: All pull requests MUST be reviewed for:
- Constitution principle compliance
- Test coverage and test-first evidence
- Security validation at boundaries
- Performance impact assessment
- Documentation completeness

## Governance

**Constitution Authority**: This constitution supersedes all other development practices and style guides. In case of conflict between this constitution and other documents, the constitution takes precedence.

**Amendment Process**: 
- Constitution changes MUST increment version per semantic versioning
- MAJOR: Backward-incompatible principle removals or redefinitions
- MINOR: New principles added or materially expanded guidance
- PATCH: Clarifications, wording fixes, non-semantic refinements
- All amendments MUST include Sync Impact Report documenting affected templates and required follow-up updates
- Amendment proposals MUST be reviewed by project maintainers before adoption

**Compliance Review**: Constitution compliance MUST be verified at two gates:
1. Pre-Phase 0: Initial constitution check before research begins
2. Post-Phase 1: Design review after architecture defined

**Runtime Guidance**: Developers SHOULD consult `.github/copilot-instructions.md` for current technology stack, commands, and code style conventions. The constitution defines principles; the guidance file documents current practices.

**Enforcement**: Pull requests that violate constitution principles without documented justification MUST be rejected. Repeated violations may result in architecture review and remediation requirements.

**Version**: 1.0.0 | **Ratified**: 2025-11-13 | **Last Amended**: 2025-11-13
