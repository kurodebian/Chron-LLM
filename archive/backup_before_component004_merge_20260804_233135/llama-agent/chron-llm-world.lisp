;;;; chron-llm-world.lisp
;;;; Chron‑LLM Δ3 — World Service

(in-package :chron-llm)

;; ============================================================
;; [1] Branching Logic
;; ============================================================

(defun stage-branch-world (graph wal parent-world-id)
  "親世界線から新しい世界線を分岐させる。
WALへ :branch イベントをステージングし、新しい世界線IDを返す。"
  (let* ((new-world-id (incf (wal-world-counter wal)))
         ;; Graph Service経由で親世界の最新ノードを特定
         (parent-node (get-latest-node-in-world graph parent-world-id))
         
         ;; parent-nodeが存在する場合のみID取得 (存在しなければ 0 = Root)
         (parent-id (if parent-node
                        (ev-node-id (causal-node-event parent-node))
                        0)))

    (let ((event-node-id
           (stage-event wal
                        :branch
                        new-world-id
                        (list :parent-id parent-id
                              :parent-world parent-world-id))))
      
      (values new-world-id event-node-id))))

;; ============================================================
;; [2] World Query
;; ============================================================

(defun get-latest-node-in-world (graph world-id)
  "指定された世界線の最新かつ健全なノードを取得する。"
  (let ((nodes (causal-graph-nodes graph))
        (latest-id nil)
        (latest-node nil))
    
    (maphash (lambda (id node)
               (when (and (eql (causal-node-causal-id node) world-id)
                          (not (eq (causal-node-class node) :fault)))
                 ;; ID比較による最新判定 (WALのインクリメントカウンタを信頼)
                 (when (or (null latest-id) (> id latest-id))
                   (setf latest-id id
                         latest-node node))))
             nodes)
    
    ;; 該当世界線のノードが存在すれば返す
    latest-node))