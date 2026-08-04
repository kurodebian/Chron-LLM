;;;; chron-llm-kernel.lisp
;;;; Chron-LLM Δ3 Kernel
;;;; Runtime <-> Kernel Boundary

(in-package :chron-llm)

;;; ============================================================
;;; DTO
;;; ============================================================

(defstruct history-entry
  (kind :unknown :type symbol)
  (text "" :type string)
  (clock 0 :type integer))

(defstruct context-object
  "LLM非依存の論理コンテキスト。"

  (system-prompt "" :type string)

  ;; 会話履歴
  (history nil :type list)

  ;; 将来のMemory Service
  (memory-context nil :type list)

  ;; 拡張用
  (metadata nil :type list))

(defstruct kernel-state

  ;; Kernelが管理する現在世界
  (world-id 0 :type integer)

  ;; :ok / :degraded
  (health :ok :type symbol)

  ;; Runtimeへ公開するView
  (context nil :type context-object))

;;; ============================================================
;;; Kernel Container
;;; ============================================================

(defclass chron-kernel ()

  ((wal
    :initarg :wal
    :reader kernel-wal)

   (graph
    :initform nil
    :accessor kernel-graph)

   ;; Runtimeは世界線を知らない
   (current-world
    :initform 100
    :accessor kernel-current-world)

   ;; 将来

   ;; memory
   ;; summary
   ;; scheduler
   ;; listeners

   ))

(defun make-chron-kernel ()

  (make-instance

   'chron-kernel

   :wal (make-instance 'write-ahead-log)))

;;; ============================================================
;;; DTO Builder
;;; ============================================================

(defun %history->dto (history)

  (mapcar

   (lambda (node)

     (let ((ev (causal-node-event node)))

       (make-history-entry

        :kind (ev-kind ev)

        :text (or (getf (ev-payload ev) :text) "")

        :clock (ev-clock ev))))

   history))

(defun kernel-build-context-view (kernel)

  (let ((graph (kernel-graph kernel)))

    (make-context-object

     :history

     (if graph

         (%history->dto

          (graph-history
           graph
           (kernel-current-world kernel)))

         nil)

     ;; Phase4以降

     :memory-context nil

     :metadata nil)))

;;; ============================================================
;;; Projection
;;; ============================================================

(defun refresh-projections (kernel)

  (setf

   (kernel-graph kernel)

   (rebuild-graph-from-wal

    (kernel-wal kernel))))

;;; ============================================================
;;; Health
;;; ============================================================

(defun kernel-health (kernel)

  (let ((graph (kernel-graph kernel)))

    (if graph

        (check-immune-status

         graph

         (kernel-current-world kernel))

        :ok)))

;;; ============================================================
;;; Internal Commit Pipeline
;;; ============================================================

(defun %kernel-commit-event
    (kernel
     kind
     payload)

  (let ((wal (kernel-wal kernel)))

    ;; Stage

    (stage-event

     wal

     kind

     (kernel-current-world kernel)

     payload)

    ;; Commit

    (multiple-value-bind (ok events)

        (commit-staged wal)

      (declare (ignore events))

      (unless ok

        (error "Kernel commit failed."))

      ;; Projection更新

      (refresh-projections kernel)

      ;; 最新状態

      (kernel-current-state kernel))))

;;; ============================================================
;;; Public API
;;; ============================================================

(defun kernel-submit-user-input
    (kernel
     text)

  (%kernel-commit-event

   kernel

   :user-message

   (list :text text)))

(defun kernel-submit-assistant-reply
    (kernel
     text)

  (%kernel-commit-event

   kernel

   :assistant-reply

   (list :text text)))

(defun kernel-current-state (kernel)

  (make-kernel-state

   :world-id

   (kernel-current-world kernel)

   :health

   (kernel-health kernel)

   :context

   (kernel-build-context-view kernel)))

;;; ============================================================
;;; World Management
;;; ============================================================

(defun kernel-create-world (kernel)

  (let* ((wal (kernel-wal kernel))

         (graph (kernel-graph kernel))

         (parent-world

          (kernel-current-world kernel))

         (new-world

          (incf (wal-world-counter wal))))

    (%kernel-commit-event

     kernel

     :branch

     (list

      :parent-world parent-world))

    (setf

     (kernel-current-world kernel)

     new-world)

    new-world))