(defpackage :chron-llm
  (:use :cl))
(in-package :chron-llm)

;;; ============================================================================
;;; Phase A/B: Event ABI & WAL Mock (シミュレーション用モック層)
;;; ============================================================================

(defstruct (event (:conc-name ev-))
  index clock causal-id kind payload)

(defclass write-ahead-log ()
  ((storage       :initform (make-array 0 :adjustable t :fill-pointer 0)
                  :accessor wal-storage)
   (clock         :initform 0
                  :accessor wal-clock)
   (staged-events :initform nil
                  :accessor wal-staged)))

(defun append-event (wal kind causal-id payload)
  (let ((ev (make-event :index    (length (wal-storage wal))
                        :clock    (incf (wal-clock wal))
                        :causal-id causal-id
                        :kind     kind
                        :payload  payload)))
    (vector-push-extend ev (wal-storage wal))))

(defun stage-event (wal kind causal-id payload)
  (push (make-event :index    (length (wal-storage wal))
                    :clock    (1+ (wal-clock wal)) ; speculative
                    :causal-id causal-id
                    :kind     kind
                    :payload  payload)
        (wal-staged wal)))

(defun discard-staged (wal)
  (setf (wal-staged wal) nil))

(defun commit-staged (wal)
  (dolist (ev (reverse (wal-staged wal)))
    (setf (ev-index ev) (length (wal-storage wal)))
    (setf (ev-clock ev) (incf (wal-clock wal)))
    (vector-push-extend ev (wal-storage wal)))
  (setf (wal-staged wal) nil))


;;; ============================================================================
;;; Phase C/D: Graph Definitions
;;; ============================================================================

(defclass causal-node ()
  ((id        :initarg :id        :reader node-id)
   (event     :initarg :event     :reader node-event)
   (class     :initarg :class     :reader node-class)
   (clock     :initarg :clock     :reader node-clock)
   (causal-id :initarg :causal-id :reader node-causal-id))
  (:documentation "WAL上のeventから持ち上げられた因果ノード。"))

(defstruct edge
  kind   ; :temporal or :causal
  from   ; node-id
  to)    ; node-id

(defstruct causal-graph
  (nodes         (make-hash-table) :read-only t)
  (edges         (make-array 0 :fill-pointer 0 :adjustable t) :read-only t)
  (causal-parents (make-hash-table) :read-only t))

(defun determine-node-class (kind)
  (case kind
    ((:user-message :assistant-reply) :dialogue)
    ((:tool-call-start :tool-call-timeout :tool-call-abort :tool-call-commit) :tool)
    ((:structural-fault :tool-fault) :fault)
    (otherwise :meta)))


;;; ============================================================================
;;; Phase D: Lifting (WAL -> DAG) & Extraction
;;; ============================================================================

(defun lift-to-graph (wal)
  (let ((graph                 (make-causal-graph))
        (last-temporal-id      nil)
        (last-healthy-causal-id (make-hash-table)))
    
    (loop for event across (wal-storage wal)
          do (let* ((node-id (ev-index event))
                    (kind    (ev-kind event))
                    (cid     (ev-causal-id event))
                    (class   (determine-node-class kind))
                    (node    (make-instance 'causal-node
                                            :id        node-id
                                            :event     event
                                            :class     class
                                            :clock     (ev-clock event)
                                            :causal-id cid)))
               
               (setf (gethash node-id (causal-graph-nodes graph)) node)
               
               (when last-temporal-id
                 (vector-push-extend (make-edge :kind :temporal
                                                :from last-temporal-id
                                                :to   node-id)
                                     (causal-graph-edges graph)))
               
               (let ((parent-id (gethash cid last-healthy-causal-id)))
                 (when parent-id
                   (vector-push-extend (make-edge :kind :causal
                                                  :from parent-id
                                                  :to   node-id)
                                       (causal-graph-edges graph))
                   (setf (gethash node-id (causal-graph-causal-parents graph))
                         parent-id)))
               
               (unless (eq class :fault)
                 (setf (gethash cid last-healthy-causal-id) node-id))
               
               (setf last-temporal-id node-id)))
    graph))

(defun clean-history (graph target-causal-id)
  (let* ((nodes-hash   (causal-graph-nodes graph))
         (parents-hash (causal-graph-causal-parents graph))
         (latest-node-id
           (loop for id being the hash-keys of nodes-hash
                 using (hash-value node)
                 when (and (eql (node-causal-id node) target-causal-id)
                           (not (eq (node-class node) :fault)))
                 maximize id)))
    (unless latest-node-id
      (return-from clean-history nil))
    
    (let ((history    nil)
          (current-id latest-node-id))
      (loop while current-id
            do (let ((node (gethash current-id nodes-hash)))
                 ;; グラフ不整合時にも安全に動作する防衛線
                 (when (and node (eq (node-class node) :dialogue))
                   (push node history))
                 (setf current-id (gethash current-id parents-hash))))
      history)))


;;; ============================================================================
;;; デバッグ・シミュレーション
;;; ============================================================================

(defun dump-wal (wal)
  (format t "~%=== [WAL RECORD] ===")
  (loop for ev across (wal-storage wal)
        do (format t "~%Idx:~2D | Clk:~2D | C-ID:~3D | Kind:~18A | Payload:~A"
                   (ev-index ev) (ev-clock ev) (ev-causal-id ev) (ev-kind ev) (ev-payload ev)))
  (format t "~%====================~%"))

(defun dump-clean-history (history causal-id)
  (format t "~%--- [Clean History for Causal-ID: ~D] ---" causal-id)
  (if (null history)
      (format t "~%  (Empty / Sealed Line)")
      (dolist (node history)
        (let ((ev (node-event node)))
          (format t "~%  [Node ~2D] (Clk:~2D) ~A: ~A"
                  (node-id node) (node-clock node) (node-class node)
                  (getf (ev-payload ev) :text)))))
  (format t "~%----------------------------------------~%"))

(defun run-causal-kernel-simulation ()
  (let ((wal (make-instance 'write-ahead-log))
        (current-causal-id 100))
    
    (format t "--- シミュレーション開始 (Causal-ID: ~D) ---~%" current-causal-id)

    (append-event wal :user-message current-causal-id '(:text "こんにちは、Blenderの調子は？"))
    (append-event wal :assistant-reply current-causal-id '(:text "好調です。応答を待機中。"))

    (append-event wal :tool-call-start current-causal-id '(:text "Blender RPC 接続開始" :target "blender"))
    (append-event wal :tool-call-timeout current-causal-id '(:text "Blender 応答なし（タイムアウト）"))

    (format t "~%[System] LLMのトークン生成ストリーム開始...~%")
    (stage-event wal :assistant-reply current-causal-id '(:text "中途半端に生成された健全なトークン列..."))
    
    (format t "[System] 警告: 25トークン目で構造的破綻 (:drift) を検知！~%")
    (discard-staged wal)
    
    (append-event wal :structural-fault current-causal-id '(:text "LLM 構造破綻による強制終了"))
    
    (let ((old-causal-id current-causal-id))
      (setf current-causal-id 101)
      (format t "~%[System] 世界線を分岐: ~D -> ~D~%" old-causal-id current-causal-id))

    (stage-event wal :assistant-reply current-causal-id
                 '(:text "申し訳ありません。接続エラーを検知したため、リトライしました。Blenderは現在正常です。"))
    (commit-staged wal)

    (dump-wal wal)
    
    (let ((graph (lift-to-graph wal)))
      (dump-clean-history (clean-history graph 100) 100)
      (dump-clean-history (clean-history graph 101) 101)))
  t)

;; 即時実行
(run-causal-kernel-simulation)
