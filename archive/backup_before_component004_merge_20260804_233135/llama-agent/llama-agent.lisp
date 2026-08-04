;;;; llama-agent.lisp
;;;; Chron‑LLM Δ3 — Unified Bootloader (Strict Separation Version)

(format t "~%=========================================~%")
(format t "🚀 Chron‑LLM Δ3 — Unified Bootloader Starting...~%")
(format t "=========================================~%")

;;; ------------------------------------------
;;; 0. 環境設定・初期化
;;; ------------------------------------------
(defparameter *system-dir* (uiop:pathname-directory-pathname *load-pathname*))

;; 🛡️ 物理層モック切り替えトグル (T: 擬似結合モード / NIL: 本物CFFI接続)
;; 境界の因果関係を1つずつ検証するため、デフォルトは T (モック優先) に設定
(defparameter *use-mock-physical-p* t)

(format t "[1/7] Loading Quicklisp & Dependencies...~%")
(let ((quicklisp-init (merge-pathnames "quicklisp/setup.lisp" (user-homedir-pathname))))
  (if (probe-file quicklisp-init)
      (load quicklisp-init)
      (error "Quicklisp が見つかりません。ホームディレクトリを確認してください。")))

(ql:quickload '(:cffi :babel))
(in-package :cl-user)

(defun load-system-file (filename)
  (let ((path (merge-pathnames filename *system-dir*)))
    (if (probe-file path)
        (progn
          (format t "  -> Loading: ~A~%" filename)
          (load path))
        (warn "  !! File not found, skipping: ~A" filename))))

;;; ------------------------------------------
;;; 1. 物理層（ffi-bindings.lisp / ffi-bindings-mock.lisp）
;;; ------------------------------------------
;; 💡 トグルに基づき、共通インターフェースを持つモックか本物かを透過的に差し替える
(format t "~%[2/7] Loading Physical Layer (~A)...~%"
        (if *use-mock-physical-p* "MOCK Mode" "FFI Bindings"))

(if *use-mock-physical-p*
    (load-system-file "ffi-bindings-mock.lisp")
    (load-system-file "ffi-bindings.lisp"))

;;; ------------------------------------------
;;; 2. 論理層（chron-llm.lisp）
;;; ------------------------------------------
;; 💡 物理層がすでに存在するため、上層ロジックを読み込んでも一切のスタイル警告が出ない！
(format t "~%[3/7] Loading Logical Layer & ABI (chron-llm)...~%")
(load-system-file "chron-llm.lisp")

;;; ------------------------------------------
;;; 3. 因果カーネル（Causal Kernel）
;;; ------------------------------------------
(format t "~%[4/7] Loading Causal Kernel...~%")
(load-system-file "chron-llm-causal.lisp")

;;; ------------------------------------------
;;; 4. 免疫系（Immune System）
;;; ------------------------------------------
(format t "~%[5/7] Loading Immune System...~%")
(load-system-file "immune-system.lisp")

;;; ------------------------------------------
;;; 5. 論理層拡張（LLM Runtime Kernel）
;;; ------------------------------------------
(format t "~%[6/7] Loading Runtime Kernel...~%")
(load-system-file "chron-llm-runtime.lisp")

;;; ------------------------------------------
;;; 6. 生成ロジック（Generate）
;;; ------------------------------------------
(format t "~%[7/7] Loading Generation Logic...~%")
(load-system-file "generate.lisp")

;;; ------------------------------------------
;;; 7. 実行層（メインループ）
;;; ------------------------------------------
(format t "~%[Final] Loading Runtime Loop...~%")
(load-system-file "run-test.lisp")

(format t "~%=========================================~%")
(format t "✨ Chron‑LLM Δ3 Unified System Booted Successfully!~%")
(format t "=========================================~%")

;;; ------------------------------------------
;;; 起動ヘルパー
;;; ------------------------------------------
(in-package :chron-llm)

(defun start-delta3 (&optional (model-path "/path/to/model.gguf"))
  "Δ3 を起動する高レベルエントリポイント。
   *use-mock-physical-p* の状態に応じて、モック駆動か本物駆動かが自動で決定される。"
  (format t "~%[Boot] Δ3 起動準備中... (Model: ~A)~%" model-path)

  (let* ((model (if *use-mock-physical-p*
                    (chron-llm::my-llama-model-load model-path)
                    (chron-llm::my-llama-model-load model-path)))  ;; 本物も同名
         (ctx   (if *use-mock-physical-p*
                    (chron-llm::my-llama-init model 4096)
                    (chron-llm::my-llama-init model 4096))))

    (format t "[Boot] モデルロード完了。メインループへ移行します。~%")
    (chron-llm::agent-main-loop ctx model)))

(defun start-delta3-stub ()
  "スタブ環境で Δ3 を起動（FFIなし、引数 nil nil 渡し）"
  (format t "~%[Boot] Δ3 スタブ環境起動...~%")
  (chron-llm::agent-main-loop nil nil))