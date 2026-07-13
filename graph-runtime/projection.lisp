(in-package :chron-r2-0-a)

(defstruct (context-node (:constructor make-context-node (id type content feedbacks)))
  (id nil :read-only t) (type nil :type keyword :read-only t)
  (content "" :type string :read-only t) (feedbacks nil :type list :read-only t))

(defun associated-evaluations (graph node-id)
  "Evaluation nodes reached through an outgoing :EVAL edge, in insertion order."
  (loop for edge in (causal-graph-edges graph)
        when (and (eq (causal-edge-type edge) :eval) (equal (causal-edge-from edge) node-id))
          collect (get-node graph (causal-edge-to edge))))

(defun project-context (graph store target-id &key (include-evaluations nil))
  "Non-destructively combine causal facts with opt-in evaluation knowledge."
  (mapcar (lambda (node)
            (make-context-node
             (causal-node-id node) (causal-node-type node)
             (or (load-payload store (causal-node-payload-ref node)) "")
             (if include-evaluations
                 (mapcar (lambda (evaluation)
                           (or (load-payload store (causal-node-payload-ref evaluation)) ""))
                         (associated-evaluations graph (causal-node-id node)))
                 nil)))
          (causal-subgraph graph target-id)))
