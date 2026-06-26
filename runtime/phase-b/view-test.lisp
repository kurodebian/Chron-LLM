(defpackage :phase-b.view-test
  (:use :cl :phase-a.history :phase-a.event :phase-b.view)
  (:export #:mc1-b))

(in-package :phase-b.view-test)

(defun mc1-b ()
  (format t "~%[MC1-B] Phase B view contract test~%")

  (let* ((h0 (make-history))
         (e1 (make-event :user "a"))
         (e2 (make-event :assistant "b"))
         (h1 (history-append (history-append h0 e1) e2))
         (h2 (history-append h1 (make-event :user "c"))))

    ;; 1. determinism
    (assert (equalp (view-type-count h1)
                    (view-type-count h1)))

    ;; 2. monotonicity
    (assert (< (view-length h1)
               (view-length h2)))

    ;; 3. prefix stability
    (assert (equal (view-first h1)
                   (view-first h2)))

    ;; 4. suffix change
    (assert (not (equal (view-last h1)
                        (view-last h2))))

    (format t "MC1-B OK~%")
    t))
