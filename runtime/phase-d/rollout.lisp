(defpackage :phase-d.rollout
  (:use :cl
        :phase-d.inference
        :phase-d.edge)
  (:export
   #:rollout
   #:rollout*))

(in-package :phase-d.rollout)

;; ------------------------------------------------------------
;; Phase D Rollout
;;
;; Deterministic graph traversal.
;;
;; R0 provides both legacy and context-aware APIs.
;; Context is reserved for future runtime extensions and is
;; intentionally unused in the current implementation.
;; ------------------------------------------------------------

(defun rollout (graph start-node steps)
  "Deterministically traverse GRAPH starting from START-NODE.

Returns the sequence of traversed edges."

  (loop
    with node = start-node
    for i from 0 below steps
    declare (ignore i)
    for edge = (next-event graph node)
    while edge
    do (setf node (edge-to edge))
    collect edge))

(defun rollout* (graph start-node steps)
  "Context-aware rollout API.

Reserved for future runtime extensions.

R0 performs the same deterministic traversal as ROLLOUT."

  (rollout graph start-node steps))