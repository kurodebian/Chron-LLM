(defparameter *n-past* 0)
(defparameter *system-prompt* "あなたは優秀なエンジニアAI、Δ3です。")

(defstruct chron-agent-state
  goal
  context
  todo
  issues)

(defparameter *current-agent-state*
  (make-chron-agent-state
    :goal "リセット機構の初回テスト"
    :context "テスト環境"
    :todo '("REPLでの動作確認")
    :issues nil))

(defun format-agent-state-to-prompt (state)
  (format nil "~%[Agent State]~%Goal: ~a~%TODO: ~{~a~^, ~}~%"
          (chron-agent-state-goal state)
          (chron-agent-state-todo state)))

(defun my-llama-reset-kv (ctx)
  (declare (ignore ctx))
  (format t "  -> [Stub] KVキャッシュを物理クリアしました~%"))

(defun my-llama-tokenize (model prompt)
  (declare (ignore model prompt))
  '(101 102 103))

(defun my-llama-decode (ctx tokens n-past)
  (declare (ignore ctx))
  (format t "  -> [Stub] ~d トークンを n-past: ~d の位置からデコードしました~%"
          (length tokens) n-past))

(defun perform-stateful-reset (ctx model)
  (format t "~&[System] リセットシーケンス開始...~%")

  (my-llama-reset-kv ctx)
  (setf *n-past* 0)

  (let ((id-tokens (my-llama-tokenize model *system-prompt*)))
    (my-llama-decode ctx id-tokens 0)
    (incf *n-past* (length id-tokens)))

  (let* ((state-str (format-agent-state-to-prompt *current-agent-state*))
         (intent-tokens (my-llama-tokenize model state-str)))
    (my-llama-decode ctx intent-tokens *n-past*)
    (incf *n-past* (length intent-tokens)))

  (format t "[System] 記憶の再構築完了。現在の n-past: ~d~%" *n-past*)
  t)

(defun get-kv-usage (ctx)
  (declare (ignore ctx))
  0.86)

(defun should-trigger-reset-p (ctx response)
  (declare (ignore response))
  (let ((usage (get-kv-usage ctx)))
    (when (>= usage 0.85)
      (format t "~&[Immune System] WARNING: KV usage high (~,2F%%). Triggering reset.~%"
              (* 100 usage))
      t)))

(defun update-agent-state-from-summary (response)
  (declare (ignore response))
  (format t "~&[Immune System] Summarizing context for memory persistency...~%")
  (setf (chron-agent-state-todo *current-agent-state*)
        (cons "要約に基づく次の行動へ移行"
              (chron-agent-state-todo *current-agent-state*))))

(defun print-reset-recovery-log ()
  (format t "~%[System] Reset complete.~%")
  (format t "Goal: ~a~%" (chron-agent-state-goal *current-agent-state*))
  (format t "Next TODO: ~a~%" (first (chron-agent-state-todo *current-agent-state*)))
  (format t "Ready to continue.~%"))

(defun my-llama-generate (ctx prompt)
  (declare (ignore ctx))
  (format nil "「~a」ですね、了解しました。(Stub)" prompt))

(defun agent-main-loop (ctx model)
  (format t "~&[System] Δ3, 起動。自律モードで待機中... (終了は :quit)~%")
  (loop
    (format t "~&> ")
    (finish-output)
    (let ((prompt (read-line)))
      (cond
        ((string= prompt ":quit")
         (format t "[System] 終了します。~%")
         (return))

        ((string= prompt ":reset")
         (perform-stateful-reset ctx model)
         (print-reset-recovery-log))

        (t
         (let ((response (my-llama-generate ctx prompt)))
           (format t "~&AI: ~a~%" response)

           (when (should-trigger-reset-p ctx response)
             (update-agent-state-from-summary response)
             (perform-stateful-reset ctx model)
             (print-reset-recovery-log))))))))
