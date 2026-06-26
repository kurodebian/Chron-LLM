(defpackage :ir-callback
  (:use :cl :cffi :ir :ir-stream)
  (:export :ir-callback))

(in-package :ir-callback)

(cffi:defcallback ir-callback :void
  ((ctx-id :pointer)
   (pos :int)
   (token :int)
   (score :float)
   (phase :int))
  (push-ir
   (make-ir :ctx-id ctx-id
            :pos pos
            :phase phase
            :token token
            :score score)))
