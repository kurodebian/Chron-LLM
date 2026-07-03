(defpackage :chronos-r0.trace
  (:use :cl :chronos-r0.history)
  (:export
   :r0-trace
   :make-r0-trace
   :r0-trace-user-text
   :r0-trace-prompt
   :r0-trace-raw
   :r0-trace-parsed
   :r0-trace-history-before
   :r0-trace-history-after
   :r0-trace-prompt-length
   :r0-trace-response-length
   :r0-trace-history-size-before
   :r0-trace-history-size-after
   :*trace-log*
   :log-trace
   :save-trace-to-file
   :dump-trace))

(in-package :chronos-r0.trace)

;; ----------------------------
;; R0 TRACE STRUCT
;; ----------------------------
(defstruct r0-trace
  user-text
  prompt
  raw
  parsed
  history-before
  history-after
  prompt-length
  response-length
  history-size-before
  history-size-after)

;; ----------------------------
;; TRACE STORAGE
;; ----------------------------
(defvar *trace-log*
  (make-array 0 :adjustable t :fill-pointer 0))

(defun log-trace (tr)
  (vector-push-extend tr *trace-log*)
  tr)

;; ----------------------------
;; SAFE SNAPSHOT EXPORT
;; ----------------------------
(defun save-trace-to-file (path)
  (let ((snapshot (coerce *trace-log* 'list)))
    (with-open-file (out path
                         :direction :output
                         :if-exists :append
                         :if-does-not-exist :create)
      (dolist (entry snapshot)
        (format out "~S~%" entry)))))

(defun dump-trace ()
  (let ((snapshot (coerce *trace-log* 'list)))
    (dolist (entry snapshot)
      (format t "~%=== TRACE ===~%~S~%" entry))))