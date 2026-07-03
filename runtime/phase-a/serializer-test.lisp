(defpackage :phase-a.serializer-test
  (:use :cl :phase-a.history :phase-a.event :phase-a.serializer)
  (:export #:mc2))


(in-package :phase-a.serializer-test)

(defun mc2 ()
  (format t "~%[MC2] Phase A serialize/deserialize contract test~%")

  (let* ((h0 (make-history))
         (e1 (make-event :user "a"))
         (e2 (make-event :assistant "b"))
         (h1 (history-append (history-append h0 e1) e2))
         (data (serialize-history h1))
         (h2 (deserialize-history data)))

    ;; 1. identity は異なる（値モデル）
    (assert (not (eq h1 h2)))

    ;; 2. 構造は同値
    (let ((s1 (history-snapshot h1))
          (s2 (history-snapshot h2)))
      (assert (= (length s1) (length s2)))
      (loop for x in s1
            for y in s2
            do (assert (event-equal x y))))

    (format t "MC2 OK~%")
    t))
