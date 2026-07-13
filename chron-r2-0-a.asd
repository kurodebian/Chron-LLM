(asdf:defsystem :chron-r2-0-a
  :description "Chron-LLM R2.0-A deterministic graph runtime core"
  :serial t
  :components ((:file "memory/store")
               (:file "graph-runtime/graph")
               (:file "graph-runtime/causal")
               (:file "graph-runtime/projection")
               (:file "graph-runtime/prefill")))

(asdf:defsystem :chron-r2-0-a/tests
  :depends-on (:chron-r2-0-a)
  :serial t
  :components ((:file "tests/r2-0-a-tests")))
