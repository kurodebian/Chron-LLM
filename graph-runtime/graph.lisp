(in-package :chron-r2-0-a)

(defstruct (causal-node (:constructor make-causal-node (id type payload-ref &optional metadata)))
  (id nil :read-only t) (type nil :type keyword :read-only t)
  (payload-ref nil :type payload-ref :read-only t) (metadata nil :read-only t))
(defstruct (causal-edge (:constructor make-causal-edge (from to type)))
  (from nil :read-only t) (to nil :read-only t) (type nil :type keyword :read-only t))
(defstruct (causal-graph (:constructor make-causal-graph (&key (nodes nil) (edges nil))))
  (nodes nil :type list) (edges nil :type list))

(defun get-node (graph id)
  (find id (causal-graph-nodes graph) :key #'causal-node-id :test #'equal))

(defun add-node! (graph node)
  (unless (causal-node-p node) (error "NODE must be a causal-node."))
  (when (get-node graph (causal-node-id node)) (error "Duplicate node id: ~S" (causal-node-id node)))
  (setf (causal-graph-nodes graph) (append (causal-graph-nodes graph) (list node))) graph)

(defun add-edge! (graph edge)
  (unless (causal-edge-p edge) (error "EDGE must be a causal-edge."))
  (unless (and (get-node graph (causal-edge-from edge)) (get-node graph (causal-edge-to edge)))
    (error "Both edge endpoints must be graph nodes."))
  (setf (causal-graph-edges graph) (append (causal-graph-edges graph) (list edge))) graph)
