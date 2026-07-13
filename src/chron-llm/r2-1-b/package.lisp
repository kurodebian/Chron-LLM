(defpackage :chron-llm/r2-1-b
  (:use :cl)
  (:export
   ;; R2.1-A
   :make-inference-observation
   :inference-observation-raw-text
   :inference-observation-prompt-text
   :inference-observation-usage-tokens
   :inference-observation-token-count
   :inference-observation-finish-reason
   :inference-observation-config
   :inference-observation-provider-metadata
   :inference-observation-error-info

   ;; R2.1-B Mock Backend
   :mock-scenario
   :register-mock-scenario
   :clear-mock-scenarios
   :find-mock-scenario-by-id
   :execute-inference

   ;; Test helpers
   :run-r2-1-b-verification))
