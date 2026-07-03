# Agent Domain Model (R1)

## Event

Event {

    id

    source ∈ {
        user,
        assistant,
        tool,
        system
    }

    payload

    metadata {
        timestamp
        seq
        lamport?
    }

}

---

## Candidate

Candidate := OperationIR

OperationIR {

    id

    source

    trigger

    intent

    payload

    constraints

    metadata

}

intent ∈ {

    append

    reflect

    tool

    memory-read

    memory-write

    recover

    summarize

}

---

## Session

Session :=

    Canonical

    Working

    Derived

    External

---

Canonical :=

    History

    Config

    MemoryRef

---

Working :=

    Candidate

    Prompt

    Backend

    IR

    Metrics

    Lookup

---

Derived :=

    Projection

    Graph

    Observation

    Summary

---

External :=

    LTM

---

## Context (R1)

Context :=

    History

    Config

    MemoryRef