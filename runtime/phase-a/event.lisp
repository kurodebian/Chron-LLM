(defpackage :phase-a.event
  (:use :cl)
  (:export
   #:make-event
   #:event-p
   #:event-type
   #:event-payload
   #:event-equal))   ;; ← これが重要

(in-package :phase-a.event)

(defstruct (event
             (:constructor %make-event (type payload)))
  type
  payload)

(defun make-event (type payload)
  (%make-event type payload))

(defun event-equal (a b)
  "Phase A structural equality for events."
  (and (event-p a)
       (event-p b)
       (equal (event-type a) (event-type b))
       (equal (event-payload a) (event-payload b))))
