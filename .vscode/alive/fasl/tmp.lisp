(defpackage :phase-d.trace
  (:use :cl
        :phase-d.edge
        :phase-d.inference
        :phase-d.graph)
  (:export
   #:trace-rollout
   #:format-edge))

(in-package :phase-d.trace)

;; ------------------------------------------------------------
;; Phase D Trace
;;
;; Human-readable deterministic traversal trace.
;;
;; Trace is a debugging and inspection utility only.
;; It performs no semantic interpretation, graph mutation,
;; or runtime execution beyond deterministic traversal.
;; ------------------------------------------------------------

(defun format-edge (edge)
  "Return a human-readable representation of EDGE."

  (format nil
          "~A -> ~A  (~A | s=~,2f)"
          (edge-from edge)
          (edge-to edge)
          (edge-relation edge)
          (edge-strength edge)))

(defun trace-rollout (graph start-node steps)
  "Print a deterministic traversal trace."

  (loop
    with node = start-node
    for step from 0 below steps
    for edge = (next-event graph node)
    while edge
    do
      (format t "~&[~D] ~A~%"
              step
              (format-edge edge))
      (setf node (edge-to edge))))
