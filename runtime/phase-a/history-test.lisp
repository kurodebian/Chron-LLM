(defpackage :phase-a.test
  (:use :cl :phase-a.history :phase-a.event)
  (:export #:mc1))


(in-package :phase-a.test)

(defun mc1 ()
  (format t "~%[MC1] Phase A structural contract test~%")

  (let* ((h0 (make-history))
         (e1 (make-event :user "a"))
         (e2 (make-event :assistant "b"))
         (h1 (history-append h0 e1))
         (h2 (history-append h1 e2)))

    ;; 1. emptiness
    (assert (history-empty-p h0))

    ;; 2. immutability / size
    (assert (history-empty-p h0)) ; unchanged
    (assert (= (history-size h1) 1))
    (assert (= (history-size h2) 2))

    ;; 3. ordering + snapshot stability
    (let ((snap (history-snapshot h2)))
      (assert (= (length snap) 2))
      (destructuring-bind (x y) snap
        (assert (equal x e1))
        (assert (equal y e2))))

    ;; 4. isolation (H0/H1/H2 の内容分離)
    (assert (history-empty-p h0))
    (assert (= (history-size h1) 1))
    (assert (= (history-size h2) 2))

    ;; 5. identity stability（ここが今回の補強）
    (assert (not (eq h0 h1)))
    (assert (not (eq h1 h2)))
    (assert (not (eq h0 h2)))

    (format t "MC1 OK~%")
    t))
