(defpackage :phase-d.graph
  (:use :cl
        :phase-d.edge)
  (:export
   #:make-graph
   #:graph-p
   #:graph-edges
   #:graph-meta
   #:graph-add-edge))

(in-package :phase-d.graph)

(defstruct graph
  edges   ;; list of EDGE
  meta)   ;; e.g. :source :phase-d, :version 1, etc.

(defun graph-add-edge (g e)
  (setf (graph-edges g)
        (cons e (graph-edges g)))
  g)
