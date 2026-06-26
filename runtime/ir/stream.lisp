(defpackage :ir-stream
  (:use :cl :ir)
  (:export :*ir-stream* :push-ir :clear-ir-stream))

(in-package :ir-stream)

(defparameter *ir-stream*
  (make-array 0 :adjustable t :fill-pointer 0))

(defun push-ir (ir)
  (vector-push-extend ir *ir-stream*))

(defun clear-ir-stream ()
  (setf *ir-stream*
        (make-array 0 :adjustable t :fill-pointer 0)))
