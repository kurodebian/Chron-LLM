(defpackage :phase-d.node
  (:use :cl
        :phase-a.event)
  (:export
   #:make-node
   #:node-p
   #:node-id
   #:node-event
   #:node-meta
   #:node-id-from-index))

(in-package :phase-d.node)

;; ------------------------------------------------------------
;; Phase D Node
;;
;; Node represents a deterministic identity anchor derived from
;; a Phase C Model.
;;
;; Guarantees:
;;   - deterministic identity
;;   - no semantic interpretation
;;   - event reference is provenance only
;;   - execution semantics belong to inference/runtime layers
;; ------------------------------------------------------------

(defstruct node
  ;; Deterministic node identifier.
  ;;
  ;; Current implementation derives identity from the
  ;; corresponding Phase C model index.
  (id nil)

  ;; Optional provenance reference.
  ;;
  ;; This field records the originating Phase A Event for
  ;; debugging and traceability only.
  ;;
  ;; It MUST NOT be used for graph execution, traversal,
  ;; or semantic interpretation.
  (event nil)

  ;; Implementation-defined metadata.
  ;;
  ;; Typical entries:
  ;;   :model-index
  ;;   :source-phase
  ;;   :created-by
  ;;
  ;; Future metadata MAY be added without changing the Node ABI.
  (meta nil
        :type list))

(defun node-id-from-index (index)
  "Return the deterministic node identifier for MODEL INDEX.

The current implementation uses the model index directly.

Future implementations MAY replace this with a persistent,
hash-based, or externally managed identifier while preserving
deterministic behavior."

  index)
