(in-package :chron-llm)

;;; ============================================================================
;;; Chron-OS Δ3: LLM Runtime Kernel (Physical Layer / Brain Stem)
;;; ============================================================================

(cffi:defcfun ("my_llama_reset_kv" %llama-reset-kv) :void
  (ctx :pointer))

;;; ============================================================================
;;; Chron-OS Δ3: Bridge to Physical Layer & Causal Sync
;;; ============================================================================

(defun sync-kv-cache (ctx model history-nodes)
  (format t "~%=== [Physical Layer] KV Cache Sync ===~%")
  (if (null history-nodes)
      (progn
        (format t "[System] 履歴ノードが空です。初期（BOS）状態として同期します。~%")
        (when ctx (%llama-reset-kv ctx))
        0)
      (let* ((texts (mapcar (lambda (node)
                              (let ((ev (causal-node-event node)))
                                (getf (ev-payload ev) :text)))
                            history-nodes))
             (prompt (format nil "~{~A~^~%~}" texts))
             (tokens (tokenize model prompt))
             (n-tokens (length tokens)))
        (format t "[Context Assembled (~D nodes)]:~%~A~%" (length history-nodes) prompt)
        (format t "[Tokenizer]: ~D tokens generated.~%" n-tokens)
        (when (and ctx tokens)
          (%llama-reset-kv ctx)
          (prefill-prompt ctx tokens)
          (format t "[LLM Runtime]: Prefill Session API Called successfully.~%"))
        (format t "======================================~%~%")
        n-tokens)))

;;; ============================================================================
;;; メインエージェントループ (因果カーネル完全適合版)
;;; ============================================================================

(defun agent-main-loop (ctx model)
  (format t "~%=========================================~%")
  (if (and ctx model)
      (format t " 🧠 Δ3 Core Activated (Physical Layer Connected)~%")
      (format t " 🧪 Δ3 Stub Mode Activated (Bypassing Physical Layer)~%"))
  (format t " Type 'exit' to terminate.~%")
  (format t "=========================================~%")

  (let ((wal (make-instance 'write-ahead-log))
        (current-causal-id 100))
    (loop
      (format t "~%User> ")
      (finish-output)
      (let ((input (read-line)))
        (when (or (string-equal input "exit") (string-equal input "quit"))
          (format t "~%[System] ターミネート信号を受信。ループを終了します。~%")
          (return))

        (when (string= input "branch-world")
          (debug-branch-world wal current-causal-id)
          (format t "~%[System] 世界線分岐を実行しました。~%")
          (continue))

        (when (> (length (string-trim '(#\Space #\Tab) input)) 0)
          (format t "~%[System] 因果律イベントをステージング中...~%")

          (stage-event wal :user-message current-causal-id (list :text input))

          (let* ((graph (lift-to-graph wal))
                 (current-nodes (clean-history graph current-causal-id)))

            (if (and ctx model)
                (progn
                  (sync-kv-cache ctx model current-nodes)

                  (let* ((prompt (format nil "<|user|>~%~A~%<|assistant|>~%" input))
                         (tokens (tokenize model prompt)))
                    (prefill-prompt ctx tokens)
                    (format t "Δ3> ")
                    (finish-output)
                    (let ((reply (generate ctx model :max-tokens 128)))
                      (stage-event wal :assistant-reply current-causal-id (list :text reply))
                      (commit-staged wal))))
                (progn
                  (format t "Δ3 (Stub)> 物理層バイパス。入力「~A」を受信。~%" input)
                  (format t "           [因果履歴ノード数: ~D 個]~%" (length current-nodes))

                  (multiple-value-bind (status entropy)
                      (check-immune-status ctx 101)
                    (format t "[Immune System] センサー判定: ~A (内部エントロピー: ~F)~%"
                            status entropy))

                  (commit-staged wal)))))))))

;;; ============================================================================
;;; 世界線分岐ユーティリティ
;;; ============================================================================

(defun push-node-to-wal (wal node causal-id)
  (let ((ev (make-event :index (length (wal-storage wal))
                        :clock (incf (wal-clock wal))
                        :causal-id causal-id
                        :kind (node-kind node)
                        :payload (list :text (node-content node)))))
    (vector-push-extend ev (wal-storage wal))
    ev))

(defun get-latest-node (wal)
  (let* ((storage (wal-storage wal))
         (last-ev (when (> (length storage) 0)
                    (aref storage (1- (length storage))))))
    (when last-ev
      (%make-node :id (ev-index last-ev)
                  :kind (ev-kind last-ev)
                  :content (getf (ev-payload last-ev) :text)
                  :parent nil
                  :worldline-id (ev-causal-id last-ev)
                  :status :active))))

(defun debug-branch-world (wal causal-id)
  (let* ((parent (get-latest-node wal))
         (new-id (incf (wal-node-counter wal)))
         (new-node (%make-node :id new-id
                               :kind :assistant-reply
                               :content "DUMMY BRANCH REPLY"
                               :parent (node-id parent)
                               :worldline-id causal-id)))
    (format t "~%[⚡ MULTIVERSE] Worldline ~A branched from ~A~%"
            causal-id (node-id parent))
    (push-node-to-wal wal new-node causal-id)
    new-node))
