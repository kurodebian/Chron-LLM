(defpackage :phase-c.model
  (:use :cl)
  (:export
   #:make-model
   #:model-p
   #:model-data
   #:model-meta
   #:model-shape))

(in-package :phase-c.model)

(defstruct model
  data
  meta
  shape)
