;; runtime/phase-d/chronos-phase-d-wal.asd
;; ASDF system for the Phase-D WAL engine (wal.lisp only).
;; Self-tests live in tests/ and load this system via asdf:load-system.
(asdf:defsystem :chronos-phase-d-wal
  :description "Chron-LLM Phase-D Commit Kernel WAL engine (ADR-001/002/003 norms)"
  :version "1.0.0"
  :components ((:file "wal")))
