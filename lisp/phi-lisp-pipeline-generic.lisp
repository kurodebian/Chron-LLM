;;;; ============================================================
;;;; Phi-4 Mini Lisp特化 6段階パイプライン（完全安定版 / DSL対応）
;;;; ============================================================

(defparameter *llama-cli* "../llama.cpp/build/bin/llama")
(defparameter *model-path* "../models/Phi-4-mini-instruct-Q6_K.gguf")
(defparameter *phi-log* "phi-log-generic.txt")

(defparameter *function-registry* nil) ;; 外部ファイルでセットされる

;;; ------------------------------------------------------------
;;; ログ出力
;;; ------------------------------------------------------------
(defun log-line (msg)
  (with-open-file (s *phi-log*
                     :direction :output
                     :if-exists :append
                     :if-does-not-exist :create)
    (format s "~A~%" msg)))

;;; ------------------------------------------------------------
;;; 最後の ASSISTANT ブロックだけ抽出
;;; ------------------------------------------------------------
(defun last-assistant (text)
  (let ((pos (search "ASSISTANT:" text :from-end t)))
    (if pos
        (subseq text (+ pos (length "ASSISTANT:")))
        text)))

;;; ------------------------------------------------------------
;;; llama.cpp 呼び出し
;;; ------------------------------------------------------------
(defun call-phi-lisp (prompt &key (role-system "") (temp 0.55) (ctx 8192))
  (let* ((full-prompt
          (if (string= role-system "")
              prompt
              (format nil "SYSTEM: ~A~%USER: ~A~%ASSISTANT:" role-system prompt)))
         (args (append
                (list "completion"
                      "-m" *model-path*
                      "-c" (princ-to-string ctx)
                      "--temp" (princ-to-string temp)
                      "-n" "2048"
                      "-no-cnv"
                      "-p" full-prompt))))
    (handler-case
        (uiop:run-program (cons *llama-cli* args)
                          :output :string
                          :error-output :string
                          :ignore-error-status t)
      (error () ""))))

;;; ------------------------------------------------------------
;;; 説明モード
;;; ------------------------------------------------------------
(defun phi-explain (user-request)
  (last-assistant
   (call-phi-lisp user-request
                  :role-system
"You are a knowledgeable Common Lisp expert. Explain the requested topic in simple Japanese. Focus on core ideas of Lisp (S式, マクロ, 再帰, 関数型の考え方など). No code unless explicitly asked."
                  :temp 0.3)))

;;; ------------------------------------------------------------
;;; 決定論的 Interpreter（AI に依存しない）
;;; ------------------------------------------------------------
(defun interpret-function-name (user-request)
  (cond
    ((or (search "fib" user-request)
         (search "フィボナッチ" user-request))
     "fib")
    ((or (search "square" user-request)
         (search "二乗" user-request))
     "square")
    ((or (search "reverse-list" user-request)
         (search "逆順" user-request)
         (search "リストを逆" user-request))
     "reverse-list")
    (t "NONE")))

;;; ------------------------------------------------------------
;;; DSL レジストリから関数を取得
;;; ------------------------------------------------------------
(defun load-function-registry ()
  (load "lisp/functions.lisp")
  *function-registry*)

(defun lookup-function (name)
  (cdr (assoc name *function-registry* :test #'string=)))

;;; ------------------------------------------------------------
;;; 6段階パイプライン（安定版 / DSL対応）
;;; ------------------------------------------------------------
(defun phi-6stage-lisp/no-log (user-request)
  (load-function-registry)
  (let* ((name (interpret-function-name user-request))
         (func (lookup-function name)))
    (if (and func (not (string= name "NONE")))
        func
        (phi-explain user-request))))
