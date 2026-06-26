(defpackage :phase-d.builder
  (:use :cl
        :phase-c.model
        :phase-d.edge
        :phase-d.rules
        :phase-d.graph)
  (:export
   #:project-graph))

(in-package :phase-d.builder)

(defun project-graph (m)
  "Phase C Model → Phase D Graph.
triples（列）を edge-list（関係）に持ち上げる。"
  (let* ((triples (model-data m))
         (edges   (build-edges-from-triples triples)))
    (make-graph
     :edges edges
     :meta  (list :source  :phase-d
                  :from    :phase-c
                  :shape   :sequence-graph
                  :version 1))))
