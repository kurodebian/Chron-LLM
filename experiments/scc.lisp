(in-package :experiment)

(defun successors (graph node)
  (mapcar #'edge-to
          (remove-if-not
           (lambda (e) (eq (edge-from e) node))
           (graph-edges graph))))

(defun predecessors (graph node)
  (mapcar #'edge-from
          (remove-if-not
           (lambda (e) (eq (edge-to e) node))
           (graph-edges graph))))

(defun dfs-order (graph nodes)
  (let ((visited (make-hash-table :test 'eq))
        (order '()))
    (labels ((visit (n)
               (unless (gethash n visited)
                 (setf (gethash n visited) t)
                 (dolist (m (successors graph n))
                   (visit m))
                 (push n order))))
      (dolist (n nodes)
        (visit n))
      order)))

(defun dfs-component (graph start visited)
  (let ((stack (list start))
        (comp '()))
    (setf (gethash start visited) t)
    (loop while stack
          for n = (pop stack) do
            (push n comp)
            (dolist (m (predecessors graph n))
              (unless (gethash m visited)
                (setf (gethash m visited) t)
                (push m stack))))
    comp))

(defun compute-sccs (graph nodes)
  "Return SCCs as a list of lists. Purely observational."
  (let* ((order (dfs-order graph nodes))
         (visited (make-hash-table :test 'eq))
         (sccs '()))
    (dolist (n order)
      (unless (gethash n visited)
        (push (dfs-component graph n visited) sccs)))
    sccs))
