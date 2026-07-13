(defpackage :phase-d.inference
  (:use :cl
        :phase-d.graph
        :phase-d.edge)
  (:export
   #:next-events
   #:next-event
   #:next-events*
   #:next-event*))

(in-package :phase-d.inference)

;; ------------------------------------------------------------
;; Phase D Inference
;;
;; Deterministic traversal over a structural graph.
;;
;; Guarantees:
;;   - deterministic edge selection
;;   - no graph mutation
;;   - no semantic interpretation
;;   - traversal depends only on graph structure
;;
;; Context-aware APIs are preserved for forward compatibility.
;; Current R0 implementation ignores CONTEXT.
;; ------------------------------------------------------------

(defun edge-order-key (edge)
  "Return a deterministic secondary ordering key."

  (list
   (getf (edge-meta edge) :from-index 0)
   (getf (edge-meta edge) :to-index 0)))

(defun edge-precedes-p (a b)
  "Deterministic edge ordering.

Priority:

  1. Higher strength
  2. Lower from-index
  3. Lower to-index"

  (cond
    ((> (edge-strength a)
        (edge-strength b))
     t)

    ((< (edge-strength a)
        (edge-strength b))
     nil)

    (t
     (let ((ka (edge-order-key a))
           (kb (edge-order-key b)))
       (or (< (first ka)
              (first kb))
           (and (= (first ka)
                   (first kb))
                (< (second ka)
                   (second kb))))))))

(defun next-events (graph node-id)
  "Return all outgoing edges from NODE-ID."

  (remove-if-not
   (lambda (edge)
     (eq (edge-from edge) node-id))
   (graph-edges graph)))

(defun next-event (graph node-id)
  "Return the highest-priority outgoing edge."

  (let ((edges (next-events graph node-id)))
    (when edges
      (car
       (sort (copy-list edges)
             #'edge-precedes-p)))))

(defun next-events* (graph node-id context)
  "Context-aware API.

CONTEXT is reserved for future extensions and is ignored in R0."

  (declare (ignore context))

  (next-events graph node-id))

(defun next-event* (graph node-id context)
  "Context-aware deterministic edge selection.

CONTEXT is reserved for future extensions and is ignored in R0."

  (declare (ignore context))

  (next-event graph node-id))