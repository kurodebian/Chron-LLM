(in-package :chron-llm)

;;; ============================================================
;;; World Service: Branching Logic
;;; ============================================================

(defun stage-branch-world (graph wal parent-world-id)
  "親世界線から新しい世界線を分岐させる"
  (let* ((new-world-id (incf (wal-world-counter wal)))
         
         ;; Graph Serviceから親ノード取得
         (parent-node (get-latest-node-in-world graph parent-world-id))
         
         ;; 親イベントID (ev-node-id を使用)
         (parent-id (if parent-node
                        (ev-node-id (causal-node-event parent-node))
                        0)))

    (let ((event-id ;; stage-eventは戻り値としてnode-idを返す
           (stage-event wal
                        :branch
                        new-world-id
                        (list :parent-id parent-id
                              :parent-world parent-world-id))))
      
      (values new-world-id event-id))))

;;; ============================================================
;;; Immune Service: Health Check
;;; ============================================================

(defun check-immune-status (graph causal-id)
  "世界線の健全性チェック (Kernel Hook)
clean-history がノードを返せば健全、NIL なら劣化と判定。"
  (let ((history (clean-history graph causal-id)))
    (if history
        :ok
        :degraded)))