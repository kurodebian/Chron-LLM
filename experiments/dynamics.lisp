(in-package :experiment)

(defun rollout* (graph start steps &optional convergence-threshold)
  "Generate a trajectory path starting from the given node for the specified number of steps.
   Optionally, stop early if the path converges within the given threshold."
  (declare (ignore graph))
  ;; next-event は未実装のため、簡易的なパス生成のみを実行
  (let ((path (list start))
        (node start))
    (dotimes (_ steps)
      ;; 次のノードを決定するロジックは後日実装予定
      (setf path (append path (list node))))
    (when (and convergence-threshold (>= (length path) 2))
      (let* ((last-nodes (subseq path (- (length path) 2)))
             (converged-p (eq (first last-nodes) (second last-nodes))))
        (when converged-p
          (return-from rollout* path))))
    path))

(defun find-attractor (graph start steps &optional convergence-threshold)
  "Find the attractor node or cycle from a given starting point.
   Optionally, stop early if the path converges within the given threshold."
  (let ((path (rollout* graph start steps convergence-threshold)))
    (if (= (length path) 1)
        (car path)
        (find-cycle path))))
