(defpackage :phase-f.inlet
  (:use :cl
        :phase-a.event
        :phase-f.frozen-config)
  (:export
   #:semantic-inlet
   #:make-semantic-inlet
   #:semantic-inlet-p
   #:semantic-inlet-value
   #:semantic-inlet-inlet-key
   #:semantic-inlet-version
   #:bind-inlet
   #:normalize-output))

(in-package :phase-f.inlet)

;; ------------------------------------------------------------
;; Semantic Inlet — the single frozen entry point (FINV-1)
;; ------------------------------------------------------------

(defstruct (semantic-inlet
             (:constructor %make-semantic-inlet (value inlet-key version))
             (:copier nil))
  (value     nil :read-only t)   ; concrete inlet reference (e.g. History)
  (inlet-key nil :read-only t)   ; keyword matching frozen-config
  (version   0   :read-only t))  ; version stamp (FINV-4)

;; ------------------------------------------------------------
;; bind-inlet — SIGMA-4 C2: bind(LLM_output → inlet)
;; ------------------------------------------------------------
;; FINV-1: Only one semantic inlet is active at a time
;; FINV-5: No semantic selection occurs outside Phase F
;; FINV-7: Inlet binding is immutable for the lifetime of F instance

(defun bind-inlet (config inlet-value)
  "Bind a concrete inlet value to a frozen config.
Returns an immutable SEMANTIC-INLET.
CONFIG must be a FROZEN-CONFIG (FINV-5: selection only in Phase F).
The returned inlet is immutable (FINV-7)."
  (assert (frozen-config-p config) (config)
          "CONFIG must be a FROZEN-CONFIG instance.")
  (%make-semantic-inlet inlet-value
                        (frozen-config-inlet-key config)
                        (frozen-config-version config)))

;; ------------------------------------------------------------
;; normalize-output — FINV-2: total, deterministic normalization
;; ------------------------------------------------------------
;; LLM output enters the system ONLY through the frozen inlet.
;; FINV-3: Normalization does NOT mutate A, C, or D contracts.

(defun normalize-output (inlet llm-output-string)
  "Normalize an LLM output string through the semantic inlet.
Returns a Phase A event suitable for history-append.
Normalization is total and deterministic (FINV-2).
Does not mutate existing A/C/D contracts (FINV-3)."
  (assert (semantic-inlet-p inlet) (inlet)
          "INLET must be a SEMANTIC-INLET instance.")
  (assert (stringp llm-output-string) (llm-output-string)
          "LLM-OUTPUT-STRING must be a string.")
  ;; Deterministic normalization:
  ;; 1. Strip leading/trailing whitespace
  ;; 2. Wrap as :assistant event (the canonical LLM role)
  (let ((normalized (string-trim '(#\Space #\Tab #\Newline #\Return)
                                 llm-output-string)))
    (make-event :assistant normalized)))