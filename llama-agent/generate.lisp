(in-package :chron-llm)

(defun run-llm-generation-with-sensors (model-path prompt max-tokens)
  "免疫系センサーを統合した推論ループの実装（Chron‑LLM Δ3 / 修正版）"
  (let ((model nil)
        (ctx   nil)
        (sampler nil))

    (unwind-protect
         (progn
           ;; 1. モデルロード（物理層）
           (multiple-value-setq (model ctx)
             (init-chron-llm model-path))

           ;; 2. トークナイズ → KVプリフィル
           (let* ((tokens (tokenize model prompt)))
             (setf *n-past* 0)
             (prefill-prompt ctx tokens))

           ;; 3. サンプラ初期化
           (setf sampler (my-sampler-init 0.7 0.9))

           (format t "~%[生成開始] -----------------------------------------~%")

           ;; 4. 生成ループ（免疫系統合）
           (block generation-loop
             (loop for step from 1 to max-tokens
                   do
                   (let ((next-id (my-sampler-sample sampler ctx)))

                     ;; EOS 検知
                     (when (my-llama-is-eog ctx next-id)
                       (format t "~%~%[終了] EOSトークンを検知 (Step: ~D)~%" step)
                       (return-from generation-loop :eos))

                     ;; トークン逐次出力
                     (cffi:with-foreign-object (buf :char 128)
                       (let ((len (my-llama-token-to-piece model next-id buf 128)))
                         (when (> len 0)
                           (format t "~A"
                                   (cffi:foreign-string-to-lisp buf :count len)))
                         (finish-output)))

                     ;; 免疫系センサー
                     (multiple-value-bind (status entropy)
                         (check-immune-status ctx next-id)
                       (cond
                         ((or (eq status :fault) (> entropy 20.0))
                          (format t "~%[致命的] Step ~D: 構造破綻検知 → KVリセット~%" step)
                          (my-llama-reset-kv ctx)
                          (return-from generation-loop :fault))
                         ((and (eq status :warning) (> entropy 5.0))
                          (format t "~%[警告] Step ~D: ドリフト検知 (Status: ~A | entropy=~,4F)~%"
                                  step status entropy))
                         ((and (eq status :healthy) (< entropy 5.0))
                          nil)))

                     ;; autoregressive decode
                     (cffi:with-foreign-object (arr :int32 1)
                       (setf (cffi:mem-ref arr :int32 0) next-id)
                       (my-llama-eval ctx arr 1 *n-past*)
                       (incf *n-past*))))))
      
      ;; 5. 終了処理
      (format t "~%--------------------------------------------------~%")
      (when sampler (my-sampler-free sampler))
      (when ctx (my-llama-free ctx))
      (when model (my-llama-model-free model)))))
