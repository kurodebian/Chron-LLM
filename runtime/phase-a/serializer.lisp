(defpackage :phase-a.serializer
  (:use :cl
        :phase-a.history
        :phase-a.event)
  (:export
   #:serialize-history
   #:deserialize-history))

(in-package :phase-a.serializer)

(defun serialize-history (h)
  "History → s-expression（構造のみを保存する境界）"
  (mapcar (lambda (e)
            (list :event
                  (event-type e)
                  (event-payload e)))
          (history-snapshot h)))

(defun deserialize-history (data)
  "s-expression → History（構造の完全再構成）"
  (let ((events
          (mapcar (lambda (x)
                    (destructuring-bind (tag type payload) x
                      (assert (eq tag :event))
                      (make-event type payload)))
                  data)))
    (make-history events)))
