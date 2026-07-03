(defpackage :chronos-r0.prompt
  (:use :cl :chronos-r0.history)
  (:export :project-to-prompt))

(in-package :chronos-r0.prompt)

(defun project-to-prompt (history)
  (let ((events (chronos-r0.history:history-events history)))
    (with-output-to-string (s)
      (format s "<|begin_of_text|>~%")
      (format s "<|start_header_id|>system<|end_header_id|>~%")
      (format s "あなたは日本語で丁寧に答えるアシスタントです。~%")
      (loop for e across events do
        (format s "<|start_header_id|>~(~A~)<|end_header_id|>~%~A~%"
                (chronos-r0.history:history-event-role e)
                (chronos-r0.history:history-event-content e)))
      (format s "<|start_header_id|>assistant<|end_header_id|>"))))
