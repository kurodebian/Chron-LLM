(defpackage :phase-c.justification
  (:use :cl)
  (:export
   #:make-justification
   #:justification-p
   #:justification-data))

(in-package :phase-c.justification)

(defstruct justification
  data)
