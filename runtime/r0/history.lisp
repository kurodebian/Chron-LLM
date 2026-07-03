(defpackage :chronos-r0.history
  (:use :cl)
  (:export
   :history
   :history-event
   :make-history
   :make-history-event
   :history-events
   :history-event-role
   :history-event-content
   :history-append
   :history-size
   :history-copy))

(in-package :chronos-r0.history)

(defstruct history-event
  role
  content)

(defstruct history
  (events (make-array 0 :adjustable t :fill-pointer 0)))

(defun history-copy (h)
  (make-history
   :events (copy-seq (history-events h))))

(defun history-append (h e)
  (vector-push-extend e (history-events h))
  h)

(defun history-size (h)
  (length (history-events h)))