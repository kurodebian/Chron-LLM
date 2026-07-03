(defpackage :ir-ffi
  (:use :cl :cffi :ir-callback)
  (:export :init-ir-bridge))

(in-package :ir-ffi)

(cffi:defcfun ("register_ir_callback" register-ir-callback) :void
  (cb :pointer))

(defun init-ir-bridge ()
  (register-ir-callback (cffi:callback ir-callback)))
