(defpackage :chron-llm/r1
  (:use :cl)
  (:import-from :chron-llm/r2-1-b
                #:make-inference-observation)
  (:import-from :chron-llm/r2-3-s
                #:physical-action-type)
  (:export
   #:cli-provider
   #:make-cli-provider
   #:fetch-observation
   #:counter-generator
   #:make-counter-generator
   #:generate-causal-id
   #:evaluate-intent
   #:run-boot-loop))
