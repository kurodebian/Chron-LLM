// config/sbcl_policy.spec
// =============================================================================
// Chron-LLM SBCL Optimization & Compiler Policy Specification
// Declaim Directives, Type Declarations, Inlining, & Memory Layout Policy
// =============================================================================

# SECTION 1: GLOBAL COMPILER OPTIMIZATION POLICIES

1.1 Dual Policy Architecture
  SBCL のコンパイル設定は、開発・検証用（Development/Auditing）と高パフォーマンス・推論ループ用（Production/Hot-Path）の2段階に明確に分離する。

1.2 Development & Auditing Policy (Safety & Invariant First)
;; Applied during build and integration test suites
(declaim (optimize (speed 1)
                   (safety 3)
                   (debug 3)
                   (space 0)
                   (compilation-speed 0)))

1.3 Production & Hot-Path Policy (Maximum Performance)
;; Applied to Phase B/C/D inner loops, vector transforms, and CFFI raw boundaries
(declaim (optimize (speed 3)
                   (safety 0)
                   (debug 0)
                   (space 0)
                   (compilation-speed 0)))

// =============================================================================

# SECTION 2: INLINING DIRECTIVES & HOT-PATH FUNCTIONS

2.1 Candidate Selector Criteria for Inlining
  - 呼び出しオーバーヘッドが関数本体の計算量を上回るアクセサ・述語関数。
  - CFFI ポインタの安全な間接参照（Pointer Offset Calculation）。
  - 型変換・キャスト関数（例: Octets ↔ Integer, Single-Float ボクシング回避用操作）。

2.2 Core Inline Declarations
(declaim (inline %unsafe-cffi-mem-aref32
                 %fast-vector-ref-int32
                 %fast-vector-ref-float
                 history-head-index
                 event-timestamp
                 proj-token-estimates
                 node-id
                 edge-weight))

;; Function definitions for inlined hot-paths
(declaim (ftype (function ((cffi:foreign-pointer) (fixnum)) (signed-byte 32))
                %unsafe-cffi-mem-aref32))
(defun %unsafe-cffi-mem-aref32 (ptr index)
  (declare (type (cffi:foreign-pointer) ptr)
           (type (fixnum) index))
  (cffi:mem-aref ptr :int32 index))

(declaim (ftype (function ((simple-array (signed-byte 32) (*)) fixnum) (signed-byte 32))
                %fast-vector-ref-int32))
(defun %fast-vector-ref-int32 (vec index)
  (declare (type (simple-array (signed-byte 32) (*)) vec)
           (type fixnum index))
  (sb-array:array-dispatch (vec)
    (aref vec index)))

// =============================================================================

# SECTION 3: TYPE DECLARATIONS & ELIMINATION OF BOXING/BOUNDS-CHECKS

3.1 FTYPE Global Signature Enforcement
  フェーズ関数および演算関数には、コンパイラが型推論を完全に解決できるよう厳格な `ftype` 宣言を付与する。

(declaim (ftype (function ((simple-array single-float (*)) fixnum) single-float)
                %fast-vector-ref-float))
(defun %fast-vector-ref-float (vec index)
  (declare (type (simple-array single-float (*)) vec)
           (type fixnum index))
  (aref vec index))

3.2 Float Boxing Elimination Directives
  SBCL が浮動小数点計算（Logits 処理 / グラフエッジ重み計算）でヒープアロケーション（Float Boxing）を発生させないための局所宣言プロトコル。

(defmacro with-unboxed-float-math ((&rest variables) &body body)
  "Enforces unboxed single-float local storage for math operations in SBCL."
  `(let ,(mapcar (lambda (v) `(,v (locally (declare (type single-float ,v)) ,v))) variables)
     (declare (type single-float ,@variables))
     ,@body))

3.3 SB-EXT Muffle Compiler Notes Isolation
  生産性向上のため、パフォーマンス意識の高いモジュール（Phase C/D/F）でのみコンパイラノート（Unboxing 報告等）を有効化し、それ以外は消音（muffle）する。

(declaim (sb-ext:muffle-conditions sb-ext:compiler-note))

// =============================================================================

# SECTION 4: SBCL MEMORY LAYOUT, PINNING & GC OPTIMIZATIONS

4.1 CFFI Boundary Object Pinning (GC Coexistence)
  C 領域（llama.cpp）に Lisp 側の配列ポインタを渡す際、GC によるオブジェクト移動を防止するために `sb-sys:with-pinned-objects` を必須とする。

(defmacro with-cffi-array-pinned ((ptr-var lisp-array) &body body)
  "Pins a contiguous Lisp simple-array in memory and exposes its foreign pointer address to CFFI."
  `(sb-sys:with-pinned-objects (,lisp-array)
     (let ((,ptr-var (sb-sys:vector-sap ,lisp-array)))
       ,@body)))

4.2 Zero-Allocation Buffer Reuse Patterns
  Phase F インレット領域で大量のトークン/Logits データをコピーする際、毎回配列を新規生成（make-array）せず、固定バッファの再利用を行う。

(defstruct (token-ring-buffer
            (:constructor make-token-ring-buffer (&key (capacity 4096)))
            (:copier nil))
  (storage (make-array 4096 :element-type '(signed-byte 32) :initial-element 0)
           :type (simple-array (signed-byte 32) (*)) :read-only t)
  (fill-pointer 0 :type fixnum)
  (capacity 4096 :type fixnum :read-only t))

(declaim (ftype (function (token-ring-buffer (signed-byte 32)) boolean)
                ring-buffer-push))
(defun ring-buffer-push (buf token)
  (declare (type token-ring-buffer buf)
           (type (signed-byte 32) token))
  (let ((fp (token-ring-buffer-fill-pointer buf))
        (cap (token-ring-buffer-capacity buf)))
    (when (< fp cap)
      (setf (aref (token-ring-buffer-storage buf) fp) token)
      (incf (token-ring-buffer-fill-pointer buf))
      t)))

// =============================================================================

# SECTION 5: COMPILER MACRO & TRANSFORM SPECIFICATIONS

5.1 Constant Propagation for Invariants Checks
  `*enable-invariant-checking*` が NIL に設定されている場合、コンパイラマクロが評価時に形式そのものを消滅させることで、コードサイズ増加を完全に防止する。

(define-compiler-macro check-invariant (&whole form id phase-id context-kind check-form &rest bindings)
  (declare (ignore id phase-id context-kind bindings))
  (if *enable-invariant-checking*
      form
      check-form))
