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
;; Phase F Semantic Inlet
;;
;; The unique frozen semantic entry point.
;;
;; Guarantees:
;;   - exactly one inlet
;;   - immutable
;;   - versioned
;;
;; FINV-1
;;   Exactly one semantic inlet is active.
;;
;; FINV-7
;;   Frozen inlet is explicit and versioned.
;; ------------------------------------------------------------

(defstruct (semantic-inlet
             (:constructor %make-semantic-inlet
                 (value inlet-key version))
             (:copier nil))
  (value nil
         :read-only t)
  (inlet-key :a
             :type keyword
             :read-only t)
  (version 0
           :type (integer 0 *)
           :read-only t))

;; ------------------------------------------------------------
;; SIGMA-4 C2
;;
;; FrozenConfig × InletValue
;;          ↓
;;   SemanticInlet
;; ------------------------------------------------------------

(defun bind-inlet (config inlet-value)
  "Bind a concrete runtime inlet to a frozen configuration."

  (assert (frozen-config-p config)
          (config)
          "CONFIG must be a FROZEN-CONFIG instance.")

  (assert inlet-value
          (inlet-value)
          "INLET-VALUE must not be NIL.")

  (%make-semantic-inlet
   inlet-value
   (frozen-config-inlet-key config)
   (frozen-config-version config)))

;; ------------------------------------------------------------
;; Output Normalization
;;
;; Deterministic normalization of LLM output.
;;
;; Phase F performs no mutation of existing runtime state.
;; ------------------------------------------------------------

(defun normalize-output (inlet llm-output-string)
  "Normalize LLM output into a canonical Phase A event.
Allows empty strings; semantic emptiness is validated by downstream pipelines."

  (assert (semantic-inlet-p inlet)
          (inlet)
          "INLET must be a SEMANTIC-INLET instance.")

  (assert (stringp llm-output-string)
          (llm-output-string)
          "LLM-OUTPUT-STRING must be a string.")

  (let ((normalized
          (string-trim
           '(#\Space #\Tab #\Newline #\Return)
           llm-output-string)))

    (make-event :assistant normalized)))
