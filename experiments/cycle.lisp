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

(defun find-recurrent-cycle (graph start steps)
  "Rollout and return the observed recurrent cycle (not a single node)."
  (let ((path (rollout* graph start steps)))
    (reverse (find-cycle path))))
