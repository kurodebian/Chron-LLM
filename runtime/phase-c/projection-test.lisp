(defpackage :phase-c.projection-test
  (:use :cl
        :phase-a.history
        :phase-a.event
        :phase-c.model
        :phase-c.projection)
  (:export #:mc1-c))

(in-package :phase-c.projection-test)

(defun mc1-c ()
  (format t "~%[MC1-C] Phase C projection contract test~%")

  (let* ((h0 (make-history))
         (e1 (make-event :user "hello"))
         (e2 (make-event :assistant "hi"))
         (h1 (history-append (history-append h0 e1) e2))
         (m  (project-model h1))
         (triples (model-data m)))

    ;; 1. triple count
    (assert (= (length triples) 2))

    ;; 2. triple structure: (role type payload)
    (destructuring-bind (r1 t1 p1) (first triples)
      (assert (eq r1 :user))
      (assert (eq t1 :user))
      (assert (equal p1 "hello")))

    (destructuring-bind (r2 t2 p2) (second triples)
      (assert (eq r2 :assistant))
      (assert (eq t2 :assistant))
      (assert (equal p2 "hi")))

    ;; 3. triple is pure (no ABI inside)
    (assert (= (length (first triples)) 3))

    ;; 4. meta correctness
    (assert (eq (getf (model-meta m) :source) :phase-c))
    (assert (eq (getf (model-meta m) :abi)    :event-v0))

    ;; 5. determinism
    (let ((m2 (project-model h1)))
      (assert (equalp (model-data m) (model-data m2)))
      (assert (equalp (model-meta m) (model-meta m2))))

    (format t "MC1-C OK~%")
    t))
