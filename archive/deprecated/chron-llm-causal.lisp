;;; ============================================================================
;;; Chron-LLM Δ3
;;; Write Ahead Log (Persistence Primitive)
;;;
;;; Responsibility
;;;   - Event staging
;;;   - Event commit
;;;   - WAL persistence
;;;   - Node / Clock allocation
;;;
;;; Non Responsibility
;;;   - Graph
;;;   - History
;;;   - Immune
;;;   - Runtime
;;;   - Prompt
;;; ============================================================================

(in-package :chron-llm)

;; ============================================================================
;; WAL
;; ============================================================================

(defclass write-ahead-log ()
  ((storage
    :initform (make-array 64
                          :adjustable t
                          :fill-pointer 0)
    :accessor wal-storage)

   (staged-events
    :initform (make-array 8
                          :adjustable t
                          :fill-pointer 0)
    :accessor wal-staged-events)

   ;; Monotonic Clock
   (clock
    :initform 0
    :accessor wal-clock)

   ;; Global Event(Node) ID
   (node-counter
    :initform 1000
    :accessor wal-node-counter)

   ;; World(Lineage) ID
   (world-counter
    :initform 100
    :accessor wal-world-counter)))

;; ============================================================================
;; Validation
;; ============================================================================

(defun invariant-check-p (wal events)
  "Commit前のWALレベル不変条件。
Phase1では常に成功。Phase2以降でValidationを追加する。"
  (declare (ignore wal events))
  t)

;; ============================================================================
;; Commit Primitive
;; ============================================================================

(defun commit-event (wal event)
  "単一イベントを永続化する。"

  ;; ----------------------------------------------------------
  ;; Future:
  ;;   (validate-event event)
  ;; ----------------------------------------------------------

  (setf (event-clock event)
        (incf (wal-clock wal)))

  (vector-push-extend
   event
   (wal-storage wal))

  event)

;; ============================================================================
;; Immediate Commit
;; ============================================================================

(defun append-event (wal kind causal-id payload)
  "即時コミット。Stageを経由しない。"

  (let ((event
         (make-event
          :node-id   (incf (wal-node-counter wal))
          :causal-id causal-id
          :kind      kind
          :payload   payload)))

    (commit-event wal event)))

;; ============================================================================
;; Stage
;; ============================================================================

(defun stage-event (wal kind causal-id payload)
  "イベントをステージ領域へ追加する。"

  (let ((event
         (make-event
          :node-id   (incf (wal-node-counter wal))
          :causal-id causal-id
          :kind      kind
          :payload   payload)))

    (vector-push-extend
     event
     (wal-staged-events wal))

    event))

(defun discard-staged (wal)
  "ステージ領域を破棄する。"

  (setf (fill-pointer (wal-staged-events wal))
        0)

  t)

(defun rollback-stage (wal)
  "ステージをロールバックする。"

  (discard-staged wal))

;; ============================================================================
;; Batch Commit
;; ============================================================================

(defun commit-staged (wal)
  "ステージされたイベントをまとめてコミットする。"

  (let ((committed-events
         (make-array 0
                     :adjustable t
                     :fill-pointer 0)))

    (when (invariant-check-p
           wal
           (wal-staged-events wal))

      (loop
        for event across (wal-staged-events wal)
        do (vector-push-extend
            (commit-event wal event)
            committed-events))

      (discard-staged wal)

      (values t committed-events))))

;; ============================================================================
;; Utility
;; ============================================================================

(defun clear-wal (wal)
  "WALを初期状態へ戻す（主にテスト用）。"

  (setf (fill-pointer (wal-storage wal)) 0)
  (setf (fill-pointer (wal-staged-events wal)) 0)

  (setf (wal-clock wal) 0)
  (setf (wal-node-counter wal) 1000)
  (setf (wal-world-counter wal) 100)

  wal)