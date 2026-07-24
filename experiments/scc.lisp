(in-package :experiment)

;; SCC Analysis Result（仕様書 v0.2 定義）
(defstruct scc-analysis-result
  components      ; (list of scc-component)
  graph-connectedness ; グラフの連結度スコア
  )

(defun successors (graph node)
  "Return the list of successor nodes for a given node."
  (mapcar #'edge-to
          (remove-if-not
           (lambda (e) (eq (edge-from e) node))
           (graph-edges graph))))

(defun predecessors (graph node)
  "Return the list of predecessor nodes for a given node."
  (mapcar #'edge-from
          (remove-if-not
           (lambda (e) (eq (edge-to e) node))
           (graph-edges graph))))

(defun dfs-order (graph nodes)
  "Perform DFS on the graph and return the order in which nodes were visited."
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
  "Find the strongly connected component starting from a given node."
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
  "Compute the strongly connected components of a given graph."
  (let* ((order (dfs-order graph nodes))
         (visited (make-hash-table :test 'eq))
         (sccs '()))
    (dolist (n order)
      (unless (gethash n visited)
        (push (dfs-component graph n visited) sccs)))
    ;; 結果を構造体として返す
    (make-scc-analysis-result
     :components (nreverse sccs)
     :graph-connectedness (/ (length nodes) (length sccs)))))
