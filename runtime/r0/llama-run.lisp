(defpackage :chronos-r0.llama
  (:use :cl)
  (:export :llama-run))

(in-package :chronos-r0.llama)

(defun llama-run (prompt)
  (uiop:run-program
   (list "/home/junu/lisp-os/llama.cpp/build/bin/llama-completion"
         "-m" "/home/junu/models/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
         "--single-turn"
         "--n-predict" "128"
         "--system-prompt" "あなたは日本語で丁寧で簡潔に答えるアシスタントです。"
         "-p" prompt)
   :output :string
   :error-output :string
   :ignore-error-status t))
