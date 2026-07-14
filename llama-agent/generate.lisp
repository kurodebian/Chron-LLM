(in-package :chron-llm)

(defun run-llm-generation-with-sensors (model-path prompt max-tokens wal)
  "免疫系センサーを統合した推論ループの実装（Chron‑LLM Δ3）"
  (let ((model nil)
        (ctx   nil)
        (sampler nil))

    (unwind-protect
         (progn
           ;; 1. モデルロード
           (multiple-value-bind (m c)
               (init-chron-llm model-path)
             (setf model m ctx c))

           ;; 2. トークナイズ → KVプリフィル
           (let* ((tokens (tokenize model prompt)))
             (setf *n-past* 0)
             (prefill-prompt ctx tokens))

           ;; 3. サンプラ初期化
           (setf sampler (my-sampler-init 0.7 0.9))

           (format t "~%[生成開始] -----------------------------------------~%")

           ;; 4. 生成ループ
           (block generation-loop
             (loop for step from 1 to max-tokens
                   do
                   (let ((next-id (my-sampler-sample sampler ctx)))

                     ;; EOS 検知
                     (when (my-llama-is-eog ctx next-id)
                       (format t "~%[終了] EOSトークンを検知 (Step: ~D)~%" step)
                       (return-from generation-loop :eos))

                     ;; トークン逐次出力
                     (cffi:with-foreign-object (buf :char 128)
                       (let ((len (my-llama-token-to-piece model next-id buf 128)))
                         (when (> len 0)
                           (format t "~A" (cffi:foreign-string-to-lisp buf :count len))
                           (finish-output))))

                     ;; 免疫系センサーによる健全性監視
                     (multiple-value-bind (status entropy)
                         (check-immune-status ctx next-id)
                       (cond
                         ;; 致命的な破綻: KVを捨て、WALをロールバックして履歴汚染を防ぐ
                         ((or (eq status :fault) (> entropy 20.0))
                          (format t "~%[致命的] Step ~D: 構造破綻 → KVリセット & Rollback~%" step)
                          (my-llama-reset-kv ctx)
                          (rollback-stage wal)
                          (return-from generation-loop :fault))

                         ;; 警告レベル: ログには残すが生成は継続
                         ((and (eq status :warning) (> entropy 5.0))
                          (format t "~%[警告] Step ~D: ドリフト検知 (Entropy: ~,4F)~%" step entropy))))

                     ;; 推論評価 (Autoregressive decode)
                     (cffi:with-foreign-object (arr :int32 1)
                       (setf (cffi:mem-ref arr :int32 0) next-id)
                       (my-llama-eval ctx arr 1 *n-past*)
                       (incf *n-past*))))))

      ;; 5. 終了処理（リソース解放）
      (format t "~%--------------------------------------------------~%")
      (when sampler (my-sampler-free sampler))
      (when ctx (my-llama-free ctx))
      (when model (my-llama-model-free model)))))