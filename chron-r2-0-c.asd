(asdf:defsystem :chron-r2-0-c
  :description "Chron-LLM R2.0-C observability object and builder foundation"
  :depends-on (:chron-r2-0-b)
  :serial t
  :components ((:file "observability/observation")))
