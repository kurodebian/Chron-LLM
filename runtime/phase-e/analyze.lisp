(defpackage :phase-e.analyze
  (:use :cl
        :phase-d.edge)
  (:export
   #:analyze-trace
   #:trace-summary))

(in-package :phase-e.analyze)

(defun analyze-trace (edges)
  "Phase D trace → minimal semantic summary (Phase E entry).
edges は rollout* が返す edge の列。"

  (let ((total (length edges))
        (reply 0)
        (temporal 0)
        (avg-strength 0.0))

    (dolist (e edges)
      (incf avg-strength (edge-strength e))
      (case (edge-relation e)
        (:reply    (incf reply))
        (:temporal (incf temporal))))

    (when (> total 0)
      (setf avg-strength (/ avg-strength total)))

    (list
     :total total
     :reply reply
     :temporal temporal
     :avg-strength avg-strength)))

(defun trace-summary (edges)
  "人間が読める形のサマリ（Phase E の観測層）"
  (destructuring-bind (&key total reply temporal avg-strength)
      (analyze-trace edges)
    (format nil
            "Trace Summary:
  total edges: ~A
  reply edges: ~A
  temporal edges: ~A
  avg strength: ~,2f"
            total reply temporal avg-strength)))
