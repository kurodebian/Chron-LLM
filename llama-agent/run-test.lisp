;;;; run-test.lisp
;;;; Chron-LLM システム全体の論理層結合テスト用ラッパー

(in-package :chron-llm)

;; ------------------------------------------------------------
;; 実行用ラッパー関数
;; ------------------------------------------------------------
(defun test-agent-loop ()
  "スタブ環境（FFIバイパス）で Δ3 自律エージェントループを安全にデバッグ走行させる。"
  (format t "~%[INFO] スタブ環境での自律エージェントループを開始します。~%")
  (format t "--------------------------------------------------~%")

  ;; chron-llm パッケージ内の agent-main-loop を厳密にチェック
  (if (fboundp 'chron-llm::agent-main-loop)
      (chron-llm::agent-main-loop nil nil)
      (format t "[ERROR] agent-main-loop が見つかりません。chron-llm-runtime.lisp のロード状態を確認してください。~%")))

;; ------------------------------------------------------------
;; ユーザー案内（ロード完了時にREPLへ表示）
;; ------------------------------------------------------------
(eval-when (:load-toplevel :execute)
  (format t "~%💡 [CHRON-LLM] 結合テスト環境の準備が完了しました。~%")
  (format t "  REPLで以下を入力すると、スタブモードで自律メインループが走ります：~%")
  (format t "  (chron-llm::test-agent-loop)~%~%"))
