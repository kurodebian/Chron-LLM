(defpackage :phase-d.graph
  (:use :cl
        :phase-d.node
        :phase-d.edge)
  (:export
   #:make-graph
   #:graph-p
   #:graph-nodes
   #:graph-edges
   #:graph-meta
   #:graph-add-node
   #:graph-add-edge))

(in-package :phase-d.graph)

;; ------------------------------------------------------------
;; Phase D Graph
;;
;; Pure structural graph produced from a Phase C Model.
;;
;; Guarantees:
;;   - deterministic construction
;;   - insertion order is preserved
;;   - contains no semantic interpretation
;;   - execution semantics belong to inference/runtime layers
;;
;; Graph is an immutable structural value except for controlled
;; construction helpers used during graph construction.
;; ------------------------------------------------------------

(defstruct graph
  ;; Ordered collection of identity anchors.
  ;; Insertion order is preserved.
  (nodes nil
         :type list)

  ;; Ordered collection of structural relations.
  ;; Insertion order is preserved.
  (edges nil
         :type list)

  ;; Implementation-defined metadata.
  ;;
  ;; Typical entries:
  ;;   :source
  ;;   :from
  ;;   :shape
  ;;   :version
  ;;
  ;; Future metadata MAY be added without changing the Graph ABI.
  (meta nil
        :type list))

(defun graph-add-node (graph node)
  "Construction helper.

Append NODE while preserving insertion order.

Returns the modified GRAPH."

  (setf (graph-nodes graph)
        (nconc (graph-nodes graph)
               (list node)))

  graph)

(defun graph-add-edge (graph edge)
  "Construction helper.

Append EDGE while preserving insertion order.

Returns the modified GRAPH."

  (setf (graph-edges graph)
        (nconc (graph-edges graph)
               (list edge)))

  graph)