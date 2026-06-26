(defpackage :phase-d.inference
  (:use :cl
        :phase-d.graph
        :phase-d.edge)
  (:export
   #:next-events
   #:next-event
   #:next-events*
   #:next-event*))

(in-package :phase-d.inference)

(defun next-events (graph node-id)
  "contextなし版（後方互換）。guardは無視して strength だけで選ぶ。"
  (remove-if-not
   (lambda (e)
     (eq (edge-from e) node-id))
   (graph-edges graph)))

(defun next-event (graph node-id)
  "contextなし版の局所推論。最も強い outgoing edge を返す。"
  (let ((outs (next-events graph node-id)))
    (when outs
      (car (sort outs #'> :key #'edge-strength)))))

(defun next-events* (graph node-id context)
  "context-aware outgoing edges。
guard があれば context を渡してフィルタする。"
  (remove-if-not
   (lambda (e)
     (and (eq (edge-from e) node-id)
          (or (null (edge-guard e))
              (funcall (edge-guard e) context))))
   (graph-edges graph)))

(defun next-event* (graph node-id context)
  "context-aware next-event。
context を考慮して有効な edge の中から、strength 最大のものを返す。"
  (let ((outs (next-events* graph node-id context)))
    (when outs
      (car (sort outs #'> :key #'edge-strength)))))
