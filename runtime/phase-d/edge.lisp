(defpackage :phase-d.edge
  (:use :cl)
  (:export
   #:make-edge
   #:edge-p
   #:edge-from
   #:edge-to
   #:edge-relation
   #:edge-strength
   #:edge-guard
   #:edge-meta))

(in-package :phase-d.edge)

;; ------------------------------------------------------------
;; Phase D Edge
;;
;; Pure structural relation between two nodes.
;;
;; Guarantees:
;;   - contains no semantic interpretation
;;   - immutable structural value
;;   - deterministic traversal metadata only
;;   - runtime policy is external to Phase D
;;
;; Guard is reserved for future runtime extensions and is not
;; used by the R0 inference layer.
;; ------------------------------------------------------------

(defstruct edge
  ;; Source node identifier.
  from

  ;; Destination node identifier.
  to

  ;; Pure structural relation.
  ;;
  ;; Typical values:
  ;;   :temporal
  ;;   :reply
  ;;   :causal
  relation

  ;; Relative traversal priority.
  strength

  ;; Reserved for future runtime policy.
  ;;
  ;; Ignored by the R0 inference layer.
  guard

  ;; Implementation-defined metadata.
  ;;
  ;; Typical entries:
  ;;   :from-index
  ;;   :to-index
  ;;   :source
  ;;   :version
  meta)