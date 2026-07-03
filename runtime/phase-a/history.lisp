(defpackage :phase-a.history
  (:use :cl :phase-a.event)
  (:export
   #:make-history
   #:history-p
   #:history-empty-p
   #:history-size
   #:history-snapshot
   #:history-append
   #:history-equal))

(in-package :phase-a.history)

;; ------------------------------------------------------------
;; History struct
;; ------------------------------------------------------------

(defstruct (history
             (:constructor %make-history (events))
             (:copier nil))
  (events '() :type list))

(defun make-history (&optional (events '()))
  (%make-history events))

(defun history-p (h)
  (typep h 'history))

(defun history-empty-p (h)
  (null (history-events h)))

(defun history-size (h)
  (length (history-events h)))

(defun history-snapshot (h)
  "Immutable, reproducible view of H."
  (copy-list (history-events h)))

(defun history-append (h entry)
  "Immutable append: returns a NEW History."
  (make-history
   (append (history-events h)
           (list entry))))

;; ------------------------------------------------------------
;; Phase A structural equality
;; ------------------------------------------------------------

(defun history-equal (h1 h2)
  "Structural equality for Phase A histories."
  (let ((e1 (history-snapshot h1))
        (e2 (history-snapshot h2)))
    (and (= (length e1) (length e2))
         (loop for x in e1
               for y in e2
               always (event-equal x y)))))
