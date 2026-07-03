# Chron-OS ↔ Agent Mapping

Agent                    Chron-OS

--------------------------------------------

Candidate          ↔      proposalIR

Validation         ↔      Δ0

Commit             ↔      Commit

History            ↔      WAL

Event              ↔      WAL Entry

Replay             ↔      replay(snapshot)

Derived            ↔      snapshot

Session            ↔      kernel-state

External           ↔      external store