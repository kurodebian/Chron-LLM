(defpackage :phase-d.builder
  (:use :cl
        :phase-c.model
        :phase-d.node
        :phase-d.rules
        :phase-d.graph)
  (:export
   #:project-graph))

(in-package :phase-d.builder)

;; ------------------------------------------------------------
;; Phase D Graph Builder
;;
;; Deterministically projects a Phase C Model into a
;; structural Phase D Graph.
;;
;; Projection consists of:
;;
;;   Model
;;      ↓
;;    Nodes
;;      ↓
;;    Edges
;;      ↓
;;     Graph
;;
;; No semantic interpretation is introduced.
;; ------------------------------------------------------------

(defun build-nodes-from-triples (triples)
  "Construct identity nodes from Phase C triples."

  (loop
    for index from 0 below (length triples)
    collect
      (make-node
       :id (node-id-from-index index)
       :meta (list
              :model-index index
              :source-phase :phase-c))))

(defun project-graph (model)
  "Project a Phase C Model into a deterministic Phase D Graph."

  (let* ((triples (model-data model))
         (nodes   (build-nodes-from-triples triples))
         (edges   (build-edges-from-triples triples)))

    (make-graph
     :nodes nodes
     :edges edges
     :meta
     (list
      :source  :phase-d
      :from    :phase-c
      :shape   :sequence-graph
      :version 0))))