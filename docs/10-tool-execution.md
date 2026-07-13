# Chron-LLM Tool Execution Specification

**Status:** Normative
**Version:** R1

---

# Purpose

Define deterministic execution of external tools.

---

# Tool Events


tool-call-start

tool-call-timeout

tool-call-abort

tool-call-commit


---

# Tool Isolation

Tool failures SHALL NOT affect dialogue execution.

Tool execution maintains the same causal-id.

---

# Retry

Retries occur only within the tool execution stream.

Dialogue execution remains unaffected.

---

# Invariants

Tool execution is causally isolated.

Dialogue replay remains deterministic.