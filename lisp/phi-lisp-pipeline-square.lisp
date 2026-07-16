;;;; ============================================================
;;;; Phi-4 Mini Lisp特化 6段階パイプライン（ファイル版・ログ分離・暴走対策版）
;;;; ============================================================

(defparameter *llama-cli* "../llama.cpp/build/bin/llama")
(defparameter *model-path* "../models/Phi-4-mini-instruct-Q6_K.gguf")
(defparameter *phi-log* "phi-log.txt")

(defun log-line (msg)
  (with-open-file (s *phi-log*
                     :direction :output
                     :if-exists :append
                     :if-does-not-exist :create)
    (format s "~A~%" msg)))

(defun extract-defun (text)
  "TEXT から最初の (defun ...) 以降だけを抽出するフィルタ。"
  (let ((pos (search "(defun" text :test #'char-equal)))
    (if pos
        (subseq text pos)
        text)))

(defun last-assistant (text)
  "TEXT から最後の ASSISTANT: 以降だけを抽出する。"
  (let* ((pos (search "ASSISTANT:" text :test #'char-equal :from-end t)))
    (if pos
        (subseq text (+ pos (length "ASSISTANT:")))
        text)))

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
                      "-n" "1024"
                      "-no-cnv"
                      "-p" full-prompt))))
    (handler-case
        (uiop:run-program (cons *llama-cli* args)
                          :output :string
                          :error-output :string
                          :ignore-error-status t)
      (error (e)
        (format t "【Error】~A~%" e)
        nil))))

(defun phi-6stage-lisp/no-log (user-request)
  (let* ((i (last-assistant
             (call-phi-lisp user-request
                            :role-system "You are an Interpreter for Common Lisp (SBCL). Clarify the request into precise requirements."
                            :temp 0.5)))
         (p (last-assistant
             (call-phi-lisp i
                            :role-system "You are a Lisp Planner. Design clean Common Lisp architecture using proper defun, let, loops etc."
                            :temp 0.5)))
         (e (last-assistant
             (call-phi-lisp p
                            :role-system "You are an Expander. Add detailed specs, edge cases, and error handling for Common Lisp."
                            :temp 0.55)))
         (c (last-assistant
             (call-phi-lisp e
                            :role-system (format nil
                                                 "You are a Lisp Coder. Write clean Common Lisp code. Follow Lisp style strictly.~%~%;; --- Few-shot Examples (Follow this style) ---~%(defun add-numbers (a b)~%  \"Add two numbers.\"~%  (+ a b))")
                            :temp 0.65)))
         (r (last-assistant
             (call-phi-lisp c
                            :role-system "You are a Lisp Refiner. Improve style, comments, and idiomatic Lisp code."
                            :temp 0.5)))
         (f (call-phi-lisp r
                  :role-system
                  "You are a strict Common Lisp (SBCL) Critic.
Return ONLY one (defun ...) form.
The function MUST be named `square`.
It MUST take one argument `x`.
It MUST return the square of `x` using (* x x).
It MUST reject non-numeric inputs with (error \"X must be a number.\").
No explanation. No prose. No markdown. Only the defun."
                  :temp 0.1))


         (assistant-body (last-assistant f))
         (final-code (extract-defun assistant-body)))

    (log-line "=== Interpreter ===") (log-line i)
    (log-line "=== Planner ===")     (log-line p)
    (log-line "=== Expander ===")    (log-line e)
    (log-line "=== Implementer ===") (log-line c)
    (log-line "=== Refiner ===")     (log-line r)
    (log-line "=== Critic (Raw) ===") (log-line f)
    (log-line "=== Critic (Assistant Body) ===") (log-line assistant-body)
    (log-line "=== Critic (Filtered Final) ===") (log-line final-code)

    final-code))

#|
(load "lisp/phi-lisp-pipeline.lisp")
(phi-6stage-lisp/no-log "引数xを受け取って二乗を返す関数 square を作ってください。")
|#
