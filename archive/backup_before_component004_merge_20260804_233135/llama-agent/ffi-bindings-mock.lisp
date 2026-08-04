;;;; ffi-bindings-mock.lisp
;;;; Chron‑LLM Δ3 — Mock Physical Layer (Pruned ABI Version)

;; 🛡️ 物理層が先読みされるため、パッケージ未定義ならこの場で仮展開する
(unless (find-package :chron-llm)
  (defpackage :chron-llm
    (:use :cl)))

(in-package :chron-llm)

;;; ------------------------------------------------------------
;;; 擬似コンテキスト・モデル構造体
;;; ------------------------------------------------------------
(defstruct mock-model
  (path "" :type string))

(defstruct mock-ctx
  (model nil)
  (context-size 4096 :type fixnum)
  (kv-past-tokens 0 :type fixnum))

;;; ------------------------------------------------------------
;;; 既存関数の修正（ABI整合版）
;;; ------------------------------------------------------------

(defun my-llama-model-load (model-path)
  "Cのモデルポインタを模したモック構造体を返す。"
  (format t "~%[MOCK-PHY] 📦 Model loading simulated for: ~A~%" model-path)
  (make-mock-model :path model-path))

(defun my-llama-init (mock-model &optional (ctx-size 4096))
  "Cのコンテキスト初期化を模したモック構造体を返す。"
  (format t "[MOCK-PHY] ⚙️ Context initialization simulated. Size: ~A~%" ctx-size)
  (make-mock-ctx :model mock-model :context-size ctx-size))

(defun my-llama-kv-cache-seq-rm (mock-ctx seq-id p-start p-end)
  "KVキャッシュの動的トリミング（シーク・巻き戻し）の擬似実行。"
  (declare (ignore seq-id p-end))
  (format t "~%[MOCK-PHY] ✂️ KV-Cache Trim -> Range: [~A, END)~%" p-start)
  (setf (mock-ctx-kv-past-tokens mock-ctx) p-start)
  0)  ;; 成功コードとして 0 を返す

(defun my-llama-eval (mock-ctx tokens n-tokens n-past)
  "トークン評価（Prefill / Generate）の擬似実行。ABI上は int32 戻り値（0=成功）。"
  (declare (ignore tokens))
  (format t "~%[MOCK-PHY] 🧠 Eval -> Tokens Count: ~A, n-past (KV Pos): ~A~%"
          n-tokens n-past)
  (setf (mock-ctx-kv-past-tokens mock-ctx) (+ n-past n-tokens))
  0)  ;; 本物と同様に 0 を成功コードとして返す

;;; ------------------------------------------------------------
;;; 不足していた ABI 関数群のモック追加
;;; ------------------------------------------------------------

(defun my-llama-model-get-vocab (model)
  (declare (ignore model))
  :mock-vocab)

(defun my-llama-tokenize (vocab buf text-len tokens n-tokens-max add-special parse-special)
  (declare (ignore vocab buf text-len tokens n-tokens-max add-special parse-special))
  ;; トークン化された要素数を返すダミー（1個のトークンに変換されたと仮定）
  1)

(defun my-llama-token-to-piece (model token-id buf buf-size)
  (declare (ignore model token-id buf buf-size))
  ;; 実際には buf に書かないが、0バイト書き込みとして扱う
  0)

(defun my-llama-is-eog (ctx token-id)
  (declare (ignore ctx token-id))
  ;; 常に偽（End of Generation ではない）を返すことで生成ループを維持
  nil)

(defun my-sampler-init (temperature top-p)
  (format t "[MOCK-PHY] 🎲 Sampler Init -> Temp: ~A, Top-P: ~A~%" temperature top-p)
  :mock-sampler)

(defun my-sampler-sample (sampler ctx)
  (declare (ignore sampler ctx))
  ;; 常にダミートークンID「42」をサンプリングする
  42)

(defun my-sampler-free (sampler)
  (declare (ignore sampler))
  t)

(defun my-llama-free (ctx)
  (declare (ignore ctx))
  (format t "[MOCK-PHY] 🛑 Context freed.~%")
  t)

(defun my-llama-model-free (model)
  (declare (ignore model))
  (format t "[MOCK-PHY] 🛑 Model freed.~%")
  t)

(defun my-llama-reset-kv (ctx)
  (declare (ignore ctx))
  (format t "[MOCK-PHY] 🔄 KV-Cache Reset.~%")
  t)
