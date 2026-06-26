(defpackage :phase-b.view
  (:use :cl :phase-a.history :phase-a.event)
  (:export
   #:view-type-count
   #:view-length
   #:view-first
   #:view-last))

(in-package :phase-b.view)

(defun view-type-count (h)
  (let ((table (make-hash-table)))
    (dolist (e (history-snapshot h))
      (incf (gethash (event-type e) table 0)))
    table))

(defun view-length (h)
  (length (history-snapshot h)))

(defun view-first (h)
  (let ((s (history-snapshot h)))
    (when s (first s))))

(defun view-last (h)
  (let ((s (history-snapshot h)))
    (when s (car (last s)))))
