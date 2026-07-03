(defpackage :phase-d.trace
  (:use :cl
        :phase-d.edge
        :phase-d.inference
        :phase-d.graph)
  (:export
   #:trace-rollout
   #:format-edge))

(in-package :phase-d.trace)

(defun format-edge (e)
  "edge → human-readable trace line"
  (format nil "~A -> ~A  (~A | s=~,2f)"
          (edge-from e)
          (edge-to e)
          (edge-relation e)
          (edge-strength e)))

(defun trace-rollout (graph start steps)
  "rollout + observation layer（Phase Dの観測固定）"
  (loop with node = start
        for i from 0 below steps
        for e = (next-event* graph node '(:step i))
        while e
        do (progn
             (format t "~&[~D] ~A~%" i (format-edge e))
             (setf node (edge-to e)))))