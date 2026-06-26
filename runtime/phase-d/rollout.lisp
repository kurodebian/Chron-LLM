(defpackage :phase-d.rollout
  (:use :cl
        :phase-d.inference
        :phase-d.edge)
  (:export
   #:rollout
   #:rollout*))

(in-package :phase-d.rollout)

(defun rollout (graph start-node steps)
  "contextなし版（後方互換）。単純に next-event を反復する。"
  (loop with node = start-node
        for i from 0 below steps
        collect (let ((e (next-event graph node)))
                  (when e
                    (setf node (edge-to e))
                    e))))

(defun rollout* (graph start-node steps)
  "context-aware rollout。
context = (:step n) だけを持つ最小時間文脈。
guard が context を参照できる。"
  (loop with node = start-node
        with context = '(:step 0)
        for i from 0 below steps
        collect
          (let ((e (next-event* graph node context)))
            (when e
              ;; 次の node へ遷移
              (setf node (edge-to e))
              ;; context を最小更新（時間だけ進める）
              (setf context (list :step (1+ (getf context :step))))
              e))))
