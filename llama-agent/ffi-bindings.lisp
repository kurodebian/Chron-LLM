;;;; ffi-bindings.lisp
;;;; Chron‑LLM Δ3 — Pure Physical Layer (FFI Bindings)

;; 💡 物理層が創世主となり、パッケージとエクスポートシンボルを定義する
(defpackage :chron-llm
  (:use :cl)
  (:export
   :init-chron-llm
   :tokenize
   :prefill-prompt
   :generate
   :*n-past*
   :start-delta3
   :start-delta3-stub

   ;; ライフサイクル・リセット管理 ABI
   :my-llama-free
   :my-llama-model-free
   :my-llama-reset-kv

   ;; 因果カーネルABI
   :event
   :make-event
   :ev-index
   :ev-clock
   :ev-causal-id
   :ev-kind
   :ev-payload))

(in-package :chron-llm)

;; =============================================================================
;; CFFI 外部関数定義 (V3 仕様)
;; =============================================================================

(cffi:defctype llama-token :int32)

(cffi:defcfun ("my_llama_model_load" my-llama-model-load) :pointer
  (path :string))

(cffi:defcfun ("my_llama_init" my-llama-init) :pointer
  (model :pointer)
  (n-ctx :int32))

(cffi:defcfun ("my_llama_model_get_vocab" my-llama-model-get-vocab) :pointer
  (model :pointer))

(cffi:defcfun ("my_llama_eval" my-llama-eval) :int32
  (ctx :pointer)
  (tokens :pointer)
  (n-tokens :int32)
  (n-past :int32))

(cffi:defcfun ("my_llama_token_to_piece" my-llama-token-to-piece) :int32
  (model :pointer)
  (token-id :int32)
  (buf :pointer)
  (length :int32))

(cffi:defcfun ("my_llama_tokenize" my-llama-tokenize) :int32
  (vocab :pointer)
  (text :pointer)
  (text-len :int32)
  (tokens :pointer)
  (n-tokens-max :int32)
  (add-special :bool)
  (parse-special :bool))

(cffi:defcfun ("my_llama_is_eog" my-llama-is-eog) :bool
  (ctx :pointer)
  (token-id :int32))

(cffi:defcfun ("my_sampler_init" my-sampler-init) :pointer
  (temperature :float)
  (top-p :float))

(cffi:defcfun ("my_sampler_sample" my-sampler-sample) :int32
  (chain :pointer)
  (ctx :pointer))

(cffi:defcfun ("my_sampler_free" my-sampler-free) :void
  (chain :pointer))

;; =============================================================================
;; ライフサイクル・リセット管理 ABI (追加分)
;; =============================================================================

(cffi:defcfun ("my_llama_free" my-llama-free) :void
  (ctx :pointer))

(cffi:defcfun ("my_llama_model_free" my-llama-model-free) :void
  (model :pointer))

(cffi:defcfun ("my_llama_reset_kv" my-llama-reset-kv) :void
  (ctx :pointer))
