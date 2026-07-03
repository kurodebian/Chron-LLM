# Agent Runtime Specification (R1)

## Flow

Input

→ Event(user)

→ Commit

→ Replay

→ Prompt

→ Backend

→ Candidate(OperationIR)

→ Validate

→ {

    Commit(Event(assistant))

  | Commit(Event(tool))

  | Reject

  | Defer

}

→ Replay

→ Derived

---

## Validation

Validation(Candidate)

→ {

    accept

    reject

    defer

}

---

## Commit API

Commit(Event)

History++

if Event.intent ∈ {

    memory-write

    recover

}

MemoryRef++

---

## Replay API

Replay(Context)

→ Projection

→ Graph

→ Observation

→ Summary

---

## Prompt Builder

Prompt := derive(Context)

---

## Backend

LLM := CandidateGenerator(Prompt)