;;;; ============================================================
;;;; Phi-4 Mini Lisp特化 6段階パイプライン（関数生成 / 説明モード分岐版）
;;;; ============================================================

(defparameter *llama-cli* "../llama.cpp/build/bin/llama")
(defparameter *model-path* "../models/Phi-4-mini-instruct-Q6_K.gguf")
(defparameter *phi-log* "phi-log-generic.txt")

(defun log-line (msg)
  (with-open-file (s *phi-log*
                     :direction :output
                     :if-exists :append
                     :if-does-not-exist :create)
    (format s "~A~%" msg)))

;;; ------------------------------------------------------------
;;; defun抽出フィルタ（括弧バランスで正確に切り出す）
;;; ------------------------------------------------------------
(defun extract-defun (text)
  (let ((pos (search "(defun" text :test #'char-equal)))
    (if (null pos)
        text
        (let* ((sub (subseq text pos))
               (end (loop for i from 0 below (length sub)
                          with count = 0
                          do (when (char= (char sub i) #\() (incf count))
                          do (when (char= (char sub i) #\)) (decf count))
                          when (and (> i 0) (= count 0))
                          return (1+ i))))
          (cond
            ;; 括弧がちゃんと閉じた場合
            (end
             (subseq sub 0 end))
            ;; 閉じなかった場合は、コードフェンスや USER までで切る
            (t
             (let* ((cut-points (remove nil
                                        (list (search "```" sub :test #'char-equal)
                                              (search "USER:" sub :test #'char-equal)
                                              (search "[end of text]" sub :test #'char-equal))))
                    (cut (and cut-points (apply #'min cut-points))))
               (if cut
                   (subseq sub 0 cut)
                   sub))))))))

;;; ------------------------------------------------------------
;;; 最後の ASSISTANT ブロックだけ抽出
;;; ------------------------------------------------------------
(defun last-assistant (text)
  (let* ((pos (search "ASSISTANT:" text :test #'char-equal :from-end t)))
    (if pos
        (subseq text (+ pos (length "ASSISTANT:")))
        text)))

;;; ------------------------------------------------------------
;;; llama.cpp 呼び出し（ChatML無効化・暴走防止）
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
      (error () nil))))

;;; ------------------------------------------------------------
;;; Interpreter の出力を構造化仕様にパース（依存ゼロ）
;;; ------------------------------------------------------------
(defun parse-spec (text)
  (let* ((lines (uiop:split-string text :separator '(#\Newline)))
         (name-line (find-if (lambda (l) (search "NAME:" l)) lines))
         (args-line (find-if (lambda (l) (search "ARGS:" l)) lines))
         (purpose-line (find-if (lambda (l) (search "PURPOSE:" l)) lines)))
    (when (or (null name-line) (null args-line) (null purpose-line))
      (error "Interpreter output malformed: ~A" text))
    (list
     :name (string-trim " "
                        (subseq name-line (+ (search "NAME:" name-line) 5)))
     :args (string-trim " "
                        (subseq args-line (+ (search "ARGS:" args-line) 5)))
     :purpose (string-trim " "
                           (subseq purpose-line (+ (search "PURPOSE:" purpose-line) 8))))))

;;; ------------------------------------------------------------
;;; 関数要求かどうかを判定する Interpreter（モード分岐用）
;;; ------------------------------------------------------------
(defparameter *interpreter-system*
  "You are an Interpreter for Common Lisp (SBCL).

If the user request explicitly asks to create or define a function,
extract NAME, ARGS, and PURPOSE.

Return EXACTLY:

NAME: <function-name>
ARGS: (<arg1> <arg2> ...)
PURPOSE: <one-sentence English description of what the function must do>

If the user request does NOT ask to create or define a function,
return:

NAME: NONE
ARGS: ()
PURPOSE: NONE

Rules:
- PURPOSE MUST NOT be empty when NAME ≠ NONE.
- Convert Japanese requests into English PURPOSE.
- DO NOT generate code.
- DO NOT generate commentary.
- DO NOT return anything except the 3 lines above.")

;;; ------------------------------------------------------------
;;; 説明モード用：LISPなどを普通に説明する
;;; ------------------------------------------------------------
(defun phi-explain (user-request)
  (last-assistant
   (call-phi-lisp user-request
                  :role-system
"You are a knowledgeable Common Lisp and programming language expert.
Explain the requested topic clearly and concisely in Japanese.
Use short paragraphs, avoid code unless explicitly requested, and focus on intuition and key ideas."
                  :temp 0.4)))

;;; ------------------------------------------------------------
;;; 6段階汎用パイプライン（関数生成モード）
;;; ------------------------------------------------------------
(defun phi-6stage-lisp/no-log (user-request)
  (let* (;; 0. Interpreter（まずモード判定）
         (i (last-assistant
             (call-phi-lisp user-request
                            :role-system *interpreter-system*
                            :temp 0.3)))
         (spec (parse-spec i))
         (name (getf spec :name))
         (args (getf spec :args))
         (purpose (getf spec :purpose)))

    ;; 関数要求でない場合は説明モードへフォールバック
    (when (string= name "NONE")
      (let ((answer (phi-explain user-request)))
        (log-line "=== Interpreter Output (NON-FUNC) ===")
        (log-line i)
        (log-line "=== Explanation Mode Output ===")
        (log-line answer)
        (return-from phi-6stage-lisp/no-log answer)))

    ;; ここから先は「関数生成モード」
    (let* (;; 2〜5. 中間ステージ
           (p (last-assistant
               (call-phi-lisp i :role-system "You are a Lisp Planner." :temp 0.5)))
           (e (last-assistant
               (call-phi-lisp p :role-system "You are an Expander." :temp 0.55)))
           (c (last-assistant
               (call-phi-lisp e :role-system "You are a Lisp Coder." :temp 0.6)))
           (r (last-assistant
               (call-phi-lisp c :role-system "You are a Lisp Refiner." :temp 0.5)))

           ;; Refiner の出力から defun のみ抽出
           (refined-code (extract-defun r))

           ;; 関数名に応じて Critic SYSTEM を切り替え
           (critic-system
            (cond
              ;; fib 専用 Critic（再帰強制）
              ((string= name "fib")
               (format nil
"You are a strict Common Lisp (SBCL) Critic.
Return ONLY one (defun ...) form.

NAME must be: ~A
ARGS must be: ~A
The function MUST satisfy: ~A

Additional Required Constraints for this function:
- The implementation MUST use simple recursion.
- The base cases MUST be (n = 0) → 0 and (n = 1) → 1.
- The recursive case MUST be (+ (fib (- n 1)) (fib (- n 2))).

General Constraints:
- Use simple, idiomatic Common Lisp
- No unnecessary helper functions
- No hallucinated optimizations
- No arrays, matrices, hash-tables, or complex data structures
  unless explicitly required by the PURPOSE
- No deeply nested loops or meaningless nested forms
- No excessive recursion depth unless PURPOSE explicitly requires it
- No advanced algorithms unless PURPOSE explicitly requires them
- No extra commentary, prose, or markdown
- Do NOT use backticks, code fences, or the words USER/ASSISTANT/[end of text]
- All parentheses MUST be balanced and the code MUST be valid Common Lisp.

Return ONLY the defun."
                       name args purpose))

              ;; square 専用 Critic（単純乗算強制）
              ((string= name "square")
               (format nil
"You are a strict Common Lisp (SBCL) Critic.
Return ONLY one (defun ...) form.

NAME must be: ~A
ARGS must be: ~A
The function MUST satisfy: ~A

Additional Required Constraints for this function:
- The implementation MUST be a single expression (* x x).
- Do NOT use recursion.
- Do NOT use loops.
- Do NOT call the function itself.
- Do NOT generate any test calls or extra forms.

General Constraints:
- Use simple, idiomatic Common Lisp
- No unnecessary helper functions
- No hallucinated optimizations
- No arrays, matrices, hash-tables, or complex data structures
  unless explicitly required by the PURPOSE
- No deeply nested loops or meaningless nested forms
- No advanced algorithms unless PURPOSE explicitly requires them
- No extra commentary, prose, or markdown
- Do NOT use backticks, code fences, or the words USER/ASSISTANT/[end of text]
- All parentheses MUST be balanced and the code MUST be valid Common Lisp.

Return ONLY the defun."
                       name args purpose))

              ;; その他汎用関数用 Critic
              (t
               (format nil
"You are a strict Common Lisp (SBCL) Critic.
Return ONLY one (defun ...) form.

NAME must be: ~A
ARGS must be: ~A
The function MUST satisfy: ~A

General Constraints:
- Use simple, idiomatic Common Lisp
- No unnecessary helper functions
- No hallucinated optimizations
- No arrays, matrices, hash-tables, or complex data structures
  unless explicitly required by the PURPOSE
- No deeply nested loops or meaningless nested forms
- No excessive recursion depth unless PURPOSE explicitly requires it
- No advanced algorithms unless PURPOSE explicitly requires them
- No extra commentary, prose, or markdown
- Do NOT use backticks, code fences, or the words USER/ASSISTANT/[end of text]
- All parentheses MUST be balanced and the code MUST be valid Common Lisp.

Return ONLY the defun."
                       name args purpose))))

           (f (call-phi-lisp refined-code :role-system critic-system :temp 0.05))
           (assistant-body (last-assistant f))
           (final-code (extract-defun assistant-body)))

      ;; ログ
      (log-line "=== Interpreter Output (FUNC) ===") (log-line i)
      (log-line "=== Parsed SPEC ===") (log-line (format nil "~A" spec))
      (log-line "=== Critic (Raw) ===") (log-line f)
      (log-line "=== Critic (Filtered Final) ===") (log-line final-code)

      final-code)))
