(defpackage :llama-engine
  (:use :cl :cffi)
  (:export :load-model
           :init-context
           :llama-run
           :*model*
           :*ctx*))

(in-package :llama-engine)

;; C 関数バインディング
(cffi:defcfun ("llama_model_load_simple" %llama-model-load-simple)
    :pointer
  (path :string))

(cffi:defcfun ("llama_init_context_safe" %llama-init-context-safe)
    :pointer
  (model :pointer))

(cffi:defcfun ("llama_run_stream_simple" %llama-run-stream-simple)
    :void
  (model :pointer)
  (ctx   :pointer)
  (prompt :string))

;; グローバル
(defparameter *model* nil)
(defparameter *ctx* nil)

(defun load-model (path)
  (setf *model* (%llama-model-load-simple path)))

(defun init-context ()
  (setf *ctx* (%llama-init-context-safe *model*)))

(defun llama-run (model ctx prompt)
  (%llama-run-stream-simple model ctx prompt))
