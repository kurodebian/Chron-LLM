// bindings/llama_cffi.spec
// =============================================================================
// Chron-LLM CFFI Bridge Specification - llama.cpp C API Interface
// Foreign Function & Foreign Type Mapping for Lisp Integration
// =============================================================================

# SECTION 1: CFFI TYPE MAPPING & OPAQUE HANDLES

1.1 Primitive Type Mappings
+---------------------+-------------------+------------------------+
| C Primitive Type    | CFFI Type Keyword | Common Lisp Type       |
+---------------------+-------------------+------------------------+
| int32_t / int       | :int32 / :int     | (signed-byte 32)       |
| uint32_t            | :uint32           | (unsigned-byte 32)     |
| int64_t             | :int64            | (signed-byte 64)       |
| float               | :float            | single-float           |
| bool                | :boolean          | boolean (t / nil)      |
| char* (null-term)   | :string           | string                 |
| void* / struct ptr  | :pointer          | cffi:foreign-pointer   |
| llama_token (int32) | :int32            | (signed-byte 32)       |
| llama_pos (int32)   | :int32            | (signed-byte 32)       |
| llama_seq_id (int32)| :int32            | (signed-byte 32)       |
+---------------------+-------------------+------------------------+

1.2 Opaque Foreign Pointer Type Aliases
(cffi:defctype llama-model-handle :pointer)
(cffi:defctype llama-context-handle :pointer)
(cffi:defctype llama-vocab-handle :pointer)
(cffi:defctype llama-sampler-handle :pointer)
(cffi:defctype llama-batch-handle :pointer)

// =============================================================================

# SECTION 2: C STRUCT DEFINITIONS (cffi:defcstruct)

2.1 Model Parameters Struct
(cffi:defcstruct llama-model-params
  (n-gpu-layers       :int32)
  (main-gpu          :int32)
  (tensor-split      :pointer)   ;; const float*
  (rpc-servers       :string)    ;; const char*
  (progress-callback :pointer)   ;; llama_progress_callback
  (progress-callback-user-data :pointer)
  (kv-overrides      :pointer)   ;; const struct llama_model_kv_override*
  (vocab-only        :boolean)
  (use-mmap          :boolean)
  (use-mlock         :boolean)
  (check-tensors     :boolean))

2.2 Context Parameters Struct
(cffi:defcstruct llama-context-params
  (n-ctx             :uint32)
  (n-batch           :uint32)
  (n-ubatch          :uint32)
  (n-seq-max         :uint32)
  (n-threads         :int32)
  (n-threads-batch   :int32)
  (rope-scaling-type :int32)
  (pooling-type      :int32)
  (attention-type    :int32)
  (rope-freq-base    :float)
  (rope-freq-scale   :float)
  (yarn-ext-factor   :float)
  (yarn-attn-factor  :float)
  (yarn-beta-fast    :float)
  (yarn-beta-slow    :float)
  (yarn-orig-ctx     :uint32)
  (defrag-thold      :float)
  (cb-eval           :pointer)
  (cb-eval-user-data :pointer)
  (type-k            :int32)
  (type-v            :int32)
  (logits-all        :boolean)
  (embeddings        :boolean)
  (offload-kqv       :boolean)
  (flash-attn        :boolean)
  (no-perf           :boolean))

2.3 Batch Execution Struct
(cffi:defcstruct llama-batch
  (n-tokens :int32)
  (token    :pointer)   ;; llama_token*
  (embd     :pointer)   ;; float*
  (pos      :pointer)   ;; llama_pos*
  (n-seq-id :pointer)   ;; int32_t*
  (seq-id   :pointer)   ;; llama_seq_id**
  (logits   :pointer))  ;; int8_t*

2.4 Token Candidate Structs (for Sampler)
(cffi:defcstruct llama-token-data
  (id    :int32)        ;; llama_token
  (logit :float)
  (p     :float))

(cffi:defcstruct llama-token-data-array
  (data   :pointer)     ;; llama_token_data*
  (size   :uint64)      ;; size_t
  (selected-idx :int64) ;; int64_t
  (sorted :boolean))

// =============================================================================

# SECTION 3: CORE CFFI FUNCTION DECLARATIONS (cffi:defcfun)

3.1 System Subsystem Lifecycle
(cffi:defcfun ("llama_backend_init" %llama-backend-init) :void)
(cffi:defcfun ("llama_backend_free" %llama-backend-free) :void)

3.2 Model Default Parameter Accessors
(cffi:defcfun ("llama_model_default_params" %llama-model-default-params)
  (:struct llama-model-params))

(cffi:defcfun ("llama_context_default_params" %llama-context-default-params)
  (:struct llama-context-params))

3.3 Model Lifecycle Management
(cffi:defcfun ("llama_load_model_from_file" %llama-load-model-from-file)
  llama-model-handle
  (path-model :string)
  (params     (:struct llama-model-params)))

(cffi:defcfun ("llama_free_model" %llama-free-model) :void
  (model llama-model-handle))

3.4 Context Lifecycle Management
(cffi:defcfun ("llama_new_context_with_model" %llama-new-context-with-model)
  llama-context-handle
  (model llama-model-handle)
  (params (:struct llama-context-params)))

(cffi:defcfun ("llama_free" %llama-free-context) :void
  (ctx llama-context-handle))

(cffi:defcfun ("llama_get_model" %llama-get-model)
  llama-model-handle
  (ctx llama-context-handle))

3.5 Vocabulary & Tokenization APIs
(cffi:defcfun ("llama_model_get_vocab" %llama-model-get-vocab)
  llama-vocab-handle
  (model llama-model-handle))

(cffi:defcfun ("llama_tokenize" %llama-tokenize) :int32
  (vocab        llama-vocab-handle)
  (text         :string)
  (text-len     :int32)
  (tokens       :pointer)   ;; llama_token* output buffer
  (max-tokens   :int32)
  (add-special  :boolean)
  (parse-special :boolean))

(cffi:defcfun ("llama_token_to_piece" %llama-token-to-piece) :int32
  (vocab      llama-vocab-handle)
  (token      :int32)
  (buf        :pointer)     ;; char* output buffer
  (length     :int32)
  (lstrip     :int32)
  (special    :boolean))

3.6 Decoding & Tensor Execution
(cffi:defcfun ("llama_batch_init" %llama-batch-init)
  (:struct llama-batch)
  (n-tokens :int32)
  (embd     :int32)
  (n-seq-max :int32))

(cffi:defcfun ("llama_batch_free" %llama-batch-free) :void
  (batch (:struct llama-batch)))

(cffi:defcfun ("llama_decode" %llama-decode) :int32
  (ctx   llama-context-handle)
  (batch (:struct llama-batch)))

(cffi:defcfun ("llama_get_logits_ith" %llama-get-logits-ith) :pointer
  (ctx llama-context-handle)
  (i   :int32))             ;; returns float*

3.7 Sampler Pipeline APIs
(cffi:defcfun ("llama_sampler_chain_init" %llama-sampler-chain-init)
  llama-sampler-handle
  (params :pointer))       ;; llama_sampler_chain_params

(cffi:defcfun ("llama_sampler_chain_add" %llama-sampler-chain-add) :void
  (chain   llama-sampler-handle)
  (sampler llama-sampler-handle))

(cffi:defcfun ("llama_sampler_init_greedy" %llama-sampler-init-greedy)
  llama-sampler-handle)

(cffi:defcfun ("llama_sampler_init_temp" %llama-sampler-init-temp)
  llama-sampler-handle
  (p-temp :float))

(cffi:defcfun ("llama_sampler_sample" %llama-sampler-sample) :int32
  (smpl llama-sampler-handle)
  (ctx  llama-context-handle)
  (idx  :int32))

(cffi:defcfun ("llama_sampler_free" %llama-sampler-free) :void
  (smpl llama-sampler-handle))

// =============================================================================

# SECTION 4: MEMORY SAFETY & RAII WRAPPER PROTOCOL

4.1 Memory Boundary Invariants
  INV_CFFI_1_NO_LEAK: Any allocation via CFFI (%llama-load-model-from-file, 
                      %llama-new-context-with-model, %llama-batch-init) MUST be 
                      guaranteed to release via unwind-protect or trivial CLOS finalizers.
  INV_CFFI_2_THREAD_SAFETY: CFFI pointer objects are not thread-safe. Model handles 
                            may be shared read-only; context handles MUST NOT be accessed concurrently.
  INV_CFFI_3_FFI_ISOLATION: Foreign memory pointers must NEVER leak beyond the 
                            Phase F boundary into Phase A (History) or Phase B (Projection).

4.2 Lisp High-Level RAII Macros
(defmacro with-llama-backend (&body body)
  `(progn
     (%llama-backend-init)
     (unwind-protect
          (progn ,@body)
       (%llama-backend-free))))

(defmacro with-llama-model ((model-var path &optional params) &body body)
  (let ((p-var (gensym "PARAMS")))
    `(let* ((,p-var (or ,params (%llama-model-default-params)))
            (,model-var (%llama-load-model-from-file ,path ,p-var)))
       (when (cffi:null-pointer-p ,model-var)
         (error "Failed to load llama model from: ~A" ,path))
       (unwind-protect
            (progn ,@body)
         (%llama-free-model ,model-var)))))

(defmacro with-llama-context ((ctx-var model &optional params) &body body)
  (let ((p-var (gensym "PARAMS")))
    `(let* ((,p-var (or ,params (%llama-context-default-params)))
            (,ctx-var (%llama-new-context-with-model ,model ,p-var)))
       (when (cffi:null-pointer-p ,ctx-var)
         (error "Failed to create llama context from model handle"))
       (unwind-protect
            (progn ,@body)
         (%llama-free-context ,ctx-var)))))

// =============================================================================

# SECTION 5: CHRON-LLM INLET INTEGRATION SPECIFICATION

5.1 Foreign Buffer to ExternalRep Mapping
  - llama.cpp から抽出された Output (トークン列 ID / Logits / テキスト断片) は、
    `normalize_input` 演算の直前に C 領域から Lisp 管理領域（S 式 / Vector）へとコピ一転送される。
  - C の Raw Pointer 参照が `ExternalRep` 型内に残留することを禁止する（INV_F3 / INV_CFFI_3 準拠）。

5.2 Lisp Side Entry Protocol Signature
  lisp_normalize_foreign_token_stream : 
    (foreign-buf: :pointer, len: :int32) -> N: NormalizedRep
