# Implementation plan

1. Add SDK-boundary regressions and demonstrate v2 startup failures.
2. Replace decorator registration with a shared low-level server factory using
   typed callbacks/results. Validate inputs with jsonschema and wrap tool errors.
3. Integrate both transports, preserve category identity, skip stdio in web-only mode.
4. Raise dependency/interpreter floors, prepare both packages at 2.0.0, document compatibility.
5. Test transports, all existing suites, and fresh wheel installations. Resolve
   full/vector extras independently without downloading model/runtime assets.

## Constitution Check

Existing business libraries remain independent from protocol adapters. SDK
protocol boundaries have real client tests; no private SDK dispatch access is
used. Input validation is explicit because the low-level v2 server removed it.
Tests were written and failed before implementation (10 startup failures under
MCP 2.3.0). The user approved this migration and its test scope in the conversation.
Security/path and search behavior changes are excluded. No extra approval is
needed for the already authorized implementation. Release and merge remain
separate from local verification.

## Validation results

- MCP SDK 2.3.0, Python 3.11.18 and 3.12.14: 690 tests passed on each interpreter;
  88.48% overall coverage, 97% shared adapter coverage.
- Fresh base and server/convenience wheel installs passed stdio and web health
  smoke checks on both interpreters. Smoke checks ran outside the checkout.
- Stdio tested with auto/current and legacy connections; SSE tested with legacy
  initialization, tool calls, resource reads, invalid input, and reconnects.
- Full/vector extras resolved to 143 packages for Python 3.11. Optional vector
  runtime/model execution was not installed or tested.
- Ruff lint/format and git whitespace checks passed. Workflow YAML parsed.
- MyPy reports seven pre-existing errors in vector imports, search, configuration,
  and the web PDF route. Comparing the original source under the same environment
  confirmed these errors already existed; the original SDK adapter also had v2
  errors that this change resolves.
- Desktop-host manual interoperability and hosted CI execution remain release
  checks; this environment validated SDK clients over real local transports.
