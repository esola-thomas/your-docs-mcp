---
paths:
  - "tests/**"
---

# Testing Rules

- Use pytest with pytest-asyncio for all tests
- Use `@pytest.mark.asyncio` for async test functions
- Follow Arrange-Act-Assert structure in every test
- Use existing fixtures from conftest.py before creating new ones
- Three test tiers: `tests/contract/` (MCP protocol), `tests/integration/` (cross-module), `tests/unit/` (individual)
- Test file naming: `test_*.py`, test function naming: `test_*`
- Minimum 80% coverage, target 95%+ for new features
- Use pytest markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.contract`
- Mock external dependencies only — never mock the module under test
- Include edge cases and error paths, not just happy paths
