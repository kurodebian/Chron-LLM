(defpackage :phase-d.edge-test
  (:use :cl
        :phase-a.history
        :phase-a.event
        :phase-c.projection
        :phase-d.builder
        :phase-d.graph
        :phase-d.edge)
  (:export #:mc1-d))

(in-package :phase-d.edge-test)

(defun mc1-d ()
  (format t "~%[MC1-D] Phase D edge construction test~%")

  (let* ((h0 (make-history))
         (e1 (make-event :user "hello"))
         (e2 (make-event :assistant "hi"))
         (h1 (history-append (history-append h0 e1) e2))
         (m  (project-model h1))
         (g  (project-graph m))
         (edges (graph-edges g)))

    ;; 1. 何らかのエッジが立っている
    (assert (plusp (length edges)))

    ;; 2. temporal edge が少なくとも1本ある
    (assert (some (lambda (e)
                    (eq (edge-relation e) :temporal))
                  edges))

    ;; 3. reply edge が少なくとも1本ある（user → assistant）
    (assert (some (lambda (e)
                    (eq (edge-relation e) :reply))
                  edges))

    (format t "MC1-D OK~%")
    t))
