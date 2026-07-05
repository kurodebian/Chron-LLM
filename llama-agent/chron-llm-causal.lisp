;;; ============================================================================
;;; Chron-OS Δ3: Causal Kernel (Logical Layer)
;;; ============================================================================

(in-package :chron-llm)

;; ------------------------------------------------------------
;; [1] WAL 管理層（クラス定義と基本操作）
;; ------------------------------------------------------------
(defclass write-ahead-log ()
  ((storage       :initform (make-array 0 :adjustable t :fill-pointer 0)
                  :accessor wal-storage)
   (clock         :initform 0
                  :accessor wal-clock)
   (staged-events :initform nil
                  :accessor wal-staged)
   (node-counter  :initform 0
                  :accessor wal-node-counter)))

(defun append-event (wal kind causal-id payload)
  (let ((ev (make-event :index    (length (wal-storage wal))
                        :clock    (incf (wal-clock wal))
                        :causal-id causal-id
                        :kind     kind
                        :payload  payload)))
    (vector-push-extend ev (wal-storage wal))))

(defun stage-event (wal kind causal-id payload)
  (push (make-event :index    (length (wal-storage wal))
                    :clock    (1+ (wal-clock wal))
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

;; ------------------------------------------------------------
;; [2] 因果グラフデータ構造
;; ------------------------------------------------------------
(defclass causal-node ()
  ((id        :initarg :id        :reader causal-node-id)
   (event     :initarg :event     :reader causal-node-event)
   (class     :initarg :class     :reader causal-node-class)
   (clock     :initarg :clock     :reader causal-node-clock)
   (causal-id :initarg :causal-id :reader causal-node-causal-id)))

(defstruct edge kind from to)

(defstruct causal-graph
  (nodes          (make-hash-table) :read-only t)
  (edges          (make-array 0 :fill-pointer 0 :adjustable t) :read-only t)
  (causal-parents (make-hash-table) :read-only t))

(defun determine-node-class (kind)
  (case kind
    ((:user-message :assistant-reply) :dialogue)
    ((:tool-call-start :tool-call-timeout :tool-call-abort :tool-call-commit) :tool)
    ((:structural-fault :tool-fault) :fault)
    (otherwise :meta)))

;; ------------------------------------------------------------
;; [3] Lifting & Clean History
;; ------------------------------------------------------------
(defun lift-to-graph (wal)
  (let ((graph                  (make-causal-graph))
        (last-temporal-id       nil)
        (last-healthy-causal-id (make-hash-table))
        (global-last-healthy-id nil))

    (loop for event across (wal-storage wal)
          do (let* ((node-id  (ev-index event))
                    (kind     (ev-kind event))
                    (cid      (ev-causal-id event))
                    (class    (determine-node-class kind))
                    (node     (make-instance 'causal-node
                                              :id        node-id
                                              :event     event
                                              :class     class
                                              :clock     (ev-clock event)
                                              :causal-id cid)))

               ;; ノード登録
               (setf (gethash node-id (causal-graph-nodes graph)) node)

               ;; 時間エッジ
               (when last-temporal-id
                 (vector-push-extend
                  (make-edge :kind :temporal
                             :from last-temporal-id
                             :to   node-id)
                  (causal-graph-edges graph)))

               ;; 因果エッジ
               (let ((parent-id
                      (multiple-value-bind (val found)
                          (gethash cid last-healthy-causal-id)
                        (if found val global-last-healthy-id))))
                 (when parent-id
                   (vector-push-extend
                    (make-edge :kind :causal
                               :from parent-id
                               :to   node-id)
                    (causal-graph-edges graph))

                   (setf (gethash node-id (causal-graph-causal-parents graph))
                         parent-id)))

               ;; 健全ノード更新
               (unless (eq class :fault)
                 (setf (gethash cid last-healthy-causal-id) node-id)
                 (setf global-last-healthy-id node-id))

               ;; 時間系列更新
               (setf last-temporal-id node-id)))

    graph))

(defun clean-history (graph target-causal-id)
  (let* ((nodes-hash   (causal-graph-nodes graph))
         (parents-hash (causal-graph-causal-parents graph))
         (latest-node-id nil))

    ;; 最新の健全ノードを探索
    (maphash (lambda (id node)
               (when (and (eql (causal-node-causal-id node) target-causal-id)
                          (not (eq (causal-node-class node) :fault)))
                 (setf latest-node-id
                       (if latest-node-id
                           (max latest-node-id id)
                           id))))
             nodes-hash)

    ;; 対象世界線に健全ノードが無ければ NIL
    (unless latest-node-id
      (return-from clean-history nil))

    ;; 最新ノードから逆走して clean history を構築
    (let ((history nil)
          (current-id latest-node-id))

      (loop while current-id
            do (let ((node (gethash current-id nodes-hash)))
                 (when (and node
                            (eq (causal-node-class node) :dialogue))
                   (push node history))
                 (setf current-id (gethash current-id parents-hash))))

      history)))

