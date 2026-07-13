(in-package :cl-user)

(defpackage :chron-llm/r2-1-b
  (:use :cl)
  (:export
   #:inference-observation
   #:make-inference-observation
   #:inference-observation-raw-text
   #:make-bootstrap-observation))


(in-package :chron-llm/r2-1-b)


(defstruct (inference-observation
            (:constructor %make-inference-observation
                (raw-text
                 prompt-text
                 usage-tokens
                 token-count
                 finish-reason
                 config
                 provider-metadata
                 error-info)))
  "Phase 0 Observation ABI."
  raw-text
  prompt-text
  usage-tokens
  token-count
  finish-reason
  config
  provider-metadata
  error-info)


(defun make-inference-observation
    (&key
       raw-text
       prompt-text
       usage-tokens
       token-count
       finish-reason
       config
       provider-metadata
       error-info)

  (%make-inference-observation
   raw-text
   prompt-text
   usage-tokens
   token-count
   finish-reason
   config
   provider-metadata
   error-info))


(defun make-bootstrap-observation ()
  "Create the first causal fact."
  (make-inference-observation
   :raw-text "bootstrap"
   :prompt-text nil
   :usage-tokens nil
   :token-count 0
   :finish-reason :stop
   :config '(:mode :bootstrap)
   :provider-metadata '(:provider :bootstrap)
   :error-info nil))