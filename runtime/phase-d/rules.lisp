(defpackage :phase-d.rules
  (:use :cl
        :phase-c.model
        :phase-d.edge
        :phase-d.node)
  (:export
   #:build-edges-from-triples))

(in-package :phase-d.rules)

(defun make-temporal-edge (i j)
  "時系列エッジ: i → j（弱因果）"
  (let ((from-id (node-id-from-index i))
        (to-id   (node-id-from-index j)))
    (make-edge
     :from from-id
     :to   to-id
     :relation :temporal
     :strength 0.3
     :guard (lambda (ctx)
              ;; step 5以降は temporal を弱める
              (< (getf ctx :step) 5))
     :meta (list :from-index i :to-index j))))

(defun make-reply-edge (i j)
  "対話エッジ: i → j（強因果）"
  (let ((from-id (node-id-from-index i))
        (to-id   (node-id-from-index j)))
    (make-edge
     :from from-id
     :to   to-id
     :relation :reply
     :strength 0.9
     :guard nil
     :meta (list :from-index i :to-index j))))

(defun %temporal-edges (triples)
  "単純な時系列エッジ: i → i+1"
  (loop for i from 0 below (1- (length triples))
        for j = (1+ i)
        collect (make-temporal-edge i j)))

(defun %dialogue-edges (triples)
  "user → assistant の対話エッジ（最小版）"
  (loop for i from 0 below (length triples)
        for t = (nth i triples)
        for (r _type _payload) = t
        when (eq r :assistant)
        collect (let ((j (max 0 (1- i))))
                  (make-reply-edge j i))))

(defun build-edges-from-triples (triples)
  "Phase C triples → Phase D edge-list（意味規則の集合）"
  (nconc
   (%temporal-edges triples)
   (%dialogue-edges triples)))
