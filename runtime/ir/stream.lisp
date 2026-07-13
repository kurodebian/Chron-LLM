(defpackage :ir-stream
  (:use :cl
        :ir)
  (:export
   #:*ir-stream*
   #:push-ir
   #:clear-ir-stream))

(in-package :ir-stream)

;; ------------------------------------------------------------
;; IR Stream
;;
;; In-memory collection of IR observations emitted by the runtime
;; callback.
;;
;; Guarantees:
;;   - preserves callback insertion order
;;   - supports deterministic analysis
;;   - contains no semantic interpretation
;;   - non-authoritative runtime state only
;;
;; The stream is cleared explicitly between decoding runs.
;; ------------------------------------------------------------

(defparameter *ir-stream*
  (make-array 0
              :adjustable t
              :fill-pointer 0)
  "Adjustable vector containing IR observations for the current run.")

(defun push-ir (ir)
  "Append an IR observation to the current stream."

  (vector-push-extend ir *ir-stream*)

  ir)

(defun clear-ir-stream ()
  "Reset the IR stream for a new decoding run."

  (setf *ir-stream*
        (make-array 0
                    :adjustable t
                    :fill-pointer 0))

  *ir-stream*)