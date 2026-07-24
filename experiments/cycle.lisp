(in-package :experiment)

(defun find-cycle (path)
  "Given a rollout path, extract the recurrent cycle at the end."
  (let* ((rev (reverse path))
         (last-node (car rev))
         (pos (position last-node (cdr rev))))
    (if pos
        ;; cycle = suffix from first reappearance of last-node
        (subseq rev 0 (1+ pos))
        ;; no cycle detected
        (list last-node))))

(defun find-recurrent-cycle (graph start steps &optional convergence-threshold)
  "Rollout and return the observed recurrent cycle (not a single node).
   Optionally, stop early if the path converges within the given threshold."
  (let ((path (rollout* graph start steps convergence-threshold)))
    (reverse (find-cycle path))))
