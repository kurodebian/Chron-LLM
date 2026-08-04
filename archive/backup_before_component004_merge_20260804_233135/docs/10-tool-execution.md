# Chron-LLM Tool Execution Specification

**Status:** Normative
**Version:** R1

# Purpose

Define deterministic execution of external tools.

# Tool Events

- tool-call-start

- tool-call-timeout

- tool-call-abort

- tool-call-commit

Tool Events represent tool execution facts.

Tool Events become authoritative only through Commit.

# Tool Isolation

Tool failures SHALL NOT affect dialogue execution.

Tool execution maintains the same causal-id.

Tool execution SHALL NOT bypass the Commit boundary.

# Retry

Retries occur only within the tool execution stream.

Dialogue execution remains unaffected.

Retry processing SHALL NOT mutate Canonical directly.

# Invariants

Tool execution is causally isolated.

Tool execution does not bypass Commit.

Dialogue replay remains deterministic.