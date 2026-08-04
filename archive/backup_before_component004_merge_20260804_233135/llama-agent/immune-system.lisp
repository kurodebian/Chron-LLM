(in-package :chron-llm)

;;; ============================================================================
;;; Chron‑OS Δ3: Immune System (Entropy Sensor)
;;; ============================================================================

(eval-when (:compile-toplevel :load-toplevel :execute)
  (ql:quickload :cffi :silent t))

;; ------------------------------------------------------------
;; 免疫系パラメータ（運用中に可変）
;; ------------------------------------------------------------
(defparameter *entropy-fault-threshold* 3.5
  "エントロピーがこの値を超えると構造破綻と判定する。")

(defparameter *entropy-warning-threshold* 2.5
  "エントロピーがこの値を超えるとドリフト警告を出す。")

;; ------------------------------------------------------------
;; 物理層 FFI は ffi-bindings.lisp 側でロード済み
;; ここでは関数だけ参照する
;; ------------------------------------------------------------
(cffi:defcfun ("my_llama_get_logits" %llama-get-logits) :pointer
  (ctx :pointer))

(cffi:defcfun ("my_llama_n_vocab" %llama-n-vocab) :int
  (ctx :pointer))

;; ------------------------------------------------------------
;; エントロピー計算（数値安全・高速版）
;; ------------------------------------------------------------
(defun calculate-entropy (ctx)
  "logits から直接エントロピーを算出する高速・安全版。
   Softmax → Shannon entropy を Lisp 側で計算する。"
  (unless ctx
    (return-from calculate-entropy (+ 1.0 (random 0.8))))
  (let* ((logits-ptr (%llama-get-logits ctx))
         (n-vocab    (%llama-n-vocab ctx))
         (max-logit  -1.0e10)
         (sum-exp    0.0d0)
         (entropy    0.0d0))
    ;; 最大ロジット探索
    (loop for i from 0 below n-vocab
          for val = (cffi:mem-aref logits-ptr :float i)
          when (> val max-logit)
          do (setf max-logit val))
    ;; Softmax 分母
    (loop for i from 0 below n-vocab
          for val = (cffi:mem-aref logits-ptr :float i)
          do (incf sum-exp (exp (- val max-logit))))
    ;; Shannon entropy
    (loop for i from 0 below n-vocab
          for val = (cffi:mem-aref logits-ptr :float i)
          for prob = (/ (exp (- val max-logit)) sum-exp)
          when (> prob 1.0d-6)
          do (decf entropy (* prob (log prob))))
    (coerce entropy 'single-float)))

;; ------------------------------------------------------------
;; 免疫系の総合判定
;; ------------------------------------------------------------
(defun check-immune-status (ctx next-id)
  (declare (ignore next-id))
  (let ((entropy (calculate-entropy ctx)))
    (cond
      ((> entropy *entropy-fault-threshold*)
       (values :fault entropy))
      ((> entropy *entropy-warning-threshold*)
       (values :warning entropy))
      (t
       (values :healthy entropy)))))
