(defpackage :phase-d.rules
  (:use :cl
        :phase-c.model
        :phase-d.edge
        :phase-d.node)
  (:export
   #:build-edges-from-triples))

(in-package :phase-d.rules)

;; ------------------------------------------------------------
;; Phase D Edge Construction Rules
;;
;; Pure structural projection from Phase C triples to
;; Phase D relational edges.
;;
;; This layer constructs graph structure only.
;; Execution policy (guards, routing, traversal heuristics)
;; belongs to the inference/runtime layers.
;; ------------------------------------------------------------

(defun make-temporal-edge (from-index to-index)
  "Construct a temporal structural relation."

  (make-edge
   :from (node-id-from-index from-index)
   :to   (node-id-from-index to-index)
   :relation :temporal
   :strength 0.3
   :guard nil
   :meta (list
          :from-index from-index
          :to-index   to-index)))

(defun make-reply-edge (from-index to-index)
  "Construct a dialogue reply structural relation."

  (make-edge
   :from (node-id-from-index from-index)
   :to   (node-id-from-index to-index)
   :relation :reply
   :strength 0.9
   :guard nil
   :meta (list
          :from-index from-index
          :to-index   to-index)))

(defun %temporal-edges (triples)
  "Construct sequential temporal relations."

  (loop
    for from-index from 0 below (1- (length triples))
    for to-index = (1+ from-index)
    collect
      (make-temporal-edge from-index to-index)))

(defun %dialogue-edges (triples)
  "Construct minimal user → assistant reply relations."

  (loop
    for index from 0 below (length triples)
    for triple = (nth index triples)
    for (role type payload) = triple
    declare (ignore type payload)
    when (eq role :assistant)
      collect
        (make-reply-edge
         (max 0 (1- index))
         index)))

(defun build-edges-from-triples (triples)
  "Project Phase C triples into a deterministic Phase D edge list."

  (nconc
   (%temporal-edges triples)
   (%dialogue-edges triples)))