(in-package :cl-user)

;; =============================================================================
;; 1. CFFI 外部関数定義 (V3 仕様)
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
  (tokens :pointer) ; シンプルな :pointer に統一
  (n-tokens :int32)
  (n-past :int32))

(cffi:defcfun ("my_llama_token_to_piece" my-llama-token-to-piece) :int32
  (model :pointer)
  (token-id :int32)
  (buf :pointer)
  (length :int32))

(cffi:defcfun ("my_llama_tokenize" my-llama-tokenize) :int32
  (vocab :pointer)
  (text :pointer)     ; :string から :pointer に変更（生のUTF-8バイト列を直撃させる）
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

;; --- 2-pass ＆ 陽なUTF-8メモリ管理に修正した完全版 Tokenize ---
(defun tokenize (model text)
  (let* ((vocab (my-llama-model-get-vocab model))
         (bytes (babel:string-to-octets text :encoding :utf-8))
         (text-len (length bytes)))
    ;; CFFIの自動変換に頼らず、Lisp側で確保した生バイト列のポインタを渡す
    (cffi:with-foreign-pointer (buf text-len)
      (loop for i below text-len
            do (setf (cffi:mem-ref buf :unsigned-char i) (aref bytes i)))
      
      ;; パス1：必要トークン数を問い合わせ（llama.cppの仕様に基づき、負の数を abs で反転）
      (let* ((n-raw (my-llama-tokenize vocab buf text-len (cffi:null-pointer) 0 t t))
             (n-required (abs n-raw)))
        (when (zerop n-required)
          (error "Tokenize returned 0 tokens"))
        
        ;; パス2：正しいサイズのバッファを確保して実際に取得
        (cffi:with-foreign-object (arr :int32 n-required)
          (let ((n (my-llama-tokenize vocab buf text-len arr n-required t t)))
            (when (< n 0)
              (error "Tokenize failed (pass2): ~A" n))
            (loop for i below n collect (cffi:mem-aref arr :int32 i))))))))

;; --- Prefill ---
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
    (let ((sampler (my-sampler-init (float temperature 1.0f0) (float top-p 1.0f0)))
          (history-bytes '()))
      (unwind-protect
           (dotimes (step max-tokens)
             (let ((next-id (my-sampler-sample sampler ctx)))
               
               (when (my-llama-is-eog ctx next-id)
                 (return))

               (let ((bytes (print-token-stream model next-id)))
                 (when bytes
                   (push bytes history-bytes)))

               ;; Autoregressive Decode (配列ポインタとして引き渡す)
               (cffi:with-foreign-object (arr :int32 1)
                 (setf (cffi:mem-ref arr :int32 0) next-id)
                 (let ((res (my-llama-eval ctx arr 1 *n-past*)))
                   (unless (zerop res)
                     (error "Decode failed with code: ~A" res)))
                 (incf *n-past*))))
        
        (my-sampler-free sampler))
      
      (format t "~%")
      (let ((flattened (apply #'concatenate '(vector (unsigned-byte 8)) (nreverse history-bytes))))
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
