(in-package :experiment)

(defun next-event (graph node-id)
  (let ((edges (remove-if-not
                (lambda (e) (eq (edge-from e) node-id))
                (graph-edges graph))))
    (car (sort edges #'> :key #'edge-strength))))

(defun rollout* (graph start steps)
  (let ((path (list start))
        (node start))
    (dotimes (_ steps)
      (let ((e (next-event graph node)))
        (if (null e)
            (return path)
            (setf node (edge-to e)
                  path (append path (list node))))))
    path))

(defun find-attractor (graph start steps)
  (car (last (rollout* graph start steps))))
