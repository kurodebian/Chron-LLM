(asdf:defsystem :chron-r2-0-b
  :description "Chron-LLM R2.0-B deterministic World Runtime"
  :depends-on (:chron-r2-0-a)
  :serial t
  :components ((:file "world/world")
               (:file "registry/registry")))

(asdf:defsystem :chron-r2-0-b/tests
  :depends-on (:chron-r2-0-b)
  :serial t
  :components ((:file "tests/r2-0-b-tests")))
