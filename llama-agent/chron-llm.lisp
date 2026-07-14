;;;; chron-llm.lisp
;;;; Chron‑LLM Δ3 — Logical Layer & Common ABI

(in-package :chron-llm)

;; =============================================================================
;; 1. 共通データ構造 (ABI / System Types)
;; =============================================================================

;;; 永続レコード: Header(システム管理) + Payload(利用者データ)
;;; 純粋な ABI 定義。全レイヤから ev-* アクセサとして参照される。
(defstruct (event (:conc-name ev-))
  (index 0 :type integer)      ;; WAL位置
  (clock 0 :type integer)      ;; 論理時計
  (node-id 0 :type integer)    ;; 永続ID
  (causal-id 0 :type integer)  ;; 世界線ID
  (kind :unknown :type symbol) ;; イベント種別
  (payload nil :type list))    ;; ユーザーデータ

;;; 実行時ノード (旧来の互換・将来の拡張用)
(defstruct (node (:constructor %make-node))
  id
  kind
  content
  parent
  (worldline-id :wl-0 :type symbol) ; メイン世界線
  (status :active :type symbol))    ; :active / :fault

;; =============================================================================
;; 2. 状態管理 ＆ ユーティリティ
;; =============================================================================

(defparameter *n-past* 0)

(defun print-token-stream (model token-id)
  "トークンをバイト列として取得し、標準出力へダイレクトに流し込む。"
  (cffi:with-foreign-pointer (buf 64)
    (let ((len (my-llama-token-to-piece model token-id buf 64)))
      (when (> len 0)
        (let ((octets (make-array len :element-type '(unsigned-byte 8))))
          (loop for i below len
                do (setf (aref octets i) (cffi:mem-ref buf :unsigned-char i)))
          (write-sequence octets *standard-output*)
          (finish-output *standard-output*)
          octets)))))

(defun tokenize (model text)
  (let* ((vocab (my-llama-model-get-vocab model))
         (bytes (babel:string-to-octets text :encoding :utf-8))
         (text-len (length bytes)))
    (cffi:with-foreign-pointer (buf text-len)
      (loop for i below text-len
            do (setf (cffi:mem-ref buf :unsigned-char i) (aref bytes i)))
      (let* ((n-raw (my-llama-tokenize vocab buf text-len (cffi:null-pointer) 0 t t))
             (n-required (abs n-raw)))
        (when (zerop n-required)
          (error "Tokenize returned 0 tokens"))
        (cffi:with-foreign-object (arr :int32 n-required)
          (let ((n (my-llama-tokenize vocab buf text-len arr n-required t t)))
            (when (< n 0)
              (error "Tokenize failed (pass2): ~A" n))
            (loop for i below n collect (cffi:mem-aref arr :int32 i))))))))

(defun prefill-prompt (ctx tokens)
  (let ((n (length tokens)))
    (cffi:with-foreign-object (arr :int32 n)
      (loop for tok in tokens
            for i from 0
            do (setf (cffi:mem-aref arr :int32 i) tok))
      (let ((res (my-llama-eval ctx arr n *n-past*)))
        (unless (zerop res)
          (error "Prefill failed with code: ~A" res))
        (incf *n-past* n)))))

;; =============================================================================
;; 3. コア推論エンジン (ストリーミングループ)
;; =============================================================================

(defun generate (ctx model &key (max-tokens 256) (temperature 0.7) (top-p 0.9))
  (sb-int:with-float-traps-masked (:invalid :divide-by-zero :overflow)
    (let ((sampler (my-sampler-init (float temperature 1.0f0)
                                    (float top-p 1.0f0)))
          (history-bytes '()))
      (unwind-protect
           (dotimes (step max-tokens)
             (let ((next-id (my-sampler-sample sampler ctx)))
               (when (my-llama-is-eog ctx next-id)
                 (return))
               (let ((bytes (print-token-stream model next-id)))
                 (when bytes
                   (push bytes history-bytes)))
               (cffi:with-foreign-object (arr :int32 1)
                 (setf (cffi:mem-ref arr :int32 0) next-id)
                 (let ((res (my-llama-eval ctx arr 1 *n-past*)))
                   (unless (zerop res)
                     (error "Decode failed with code: ~A" res)))
                 (incf *n-past*))))
        (my-sampler-free sampler))
      (format t "~%")
      (let ((flattened (apply #'concatenate '(vector (unsigned-byte 8))
                              (nreverse history-bytes))))
        (babel:octets-to-string flattened :encoding :utf-8)))))

;; =============================================================================
;; 4. 初期化エントリーポイント
;; =============================================================================

(defun init-chron-llm (model-path &key (n-ctx 4096))
  (let* ((model (sb-int:with-float-traps-masked (:invalid :divide-by-zero :overflow)
                  (my-llama-model-load model-path)))
         (ctx   (sb-int:with-float-traps-masked (:invalid :divide-by-zero :overflow)
                  (my-llama-init model n-ctx))))
    (setf *n-past* 0)
    (values model ctx)))

#|
(load "~/quicklisp/setup.lisp")
(ql:quickload '(:cffi :babel))
(load "~/Chron-LLM/chron-llm.lisp")
(cffi:load-foreign-library #P"/home/junu/llama.cpp/build/bin/libllama_wrapper.so")
(multiple-value-bind (model ctx)
    (init-chron-llm "/home/junu/models/Phi-4-mini-instruct-Q6_K.gguf")
  (defparameter *model* model)
  (defparameter *ctx* ctx))

(defparameter *prompt* "<|user|>\nこんにちは、自己紹介をお願いします。\n<|assistant|>")
(defparameter *prompt-tokens* (tokenize *model* *prompt*))
(print *prompt-tokens*)

(setf *n-past* 0)
(prefill-prompt *ctx* *prompt-tokens*)

(generate *ctx* *model* :max-tokens 64 :temperature 0.7 :top-p 0.9)
|#
