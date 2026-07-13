(in-package :chron-r2-0-a)

;;; The mutable values below are private cells.  Public readers return copies
;;; for policy/metadata, while only the kernel commit operation can advance a
;;; head.  Graph and memory references are deliberately shared, never copied.
(defstruct (world (:constructor %make-world (id graph-ref memory-ref root-node head-cell
                                                projection-policy metadata lifecycle))
                  (:conc-name %world-))
  (id nil :read-only t)
  (graph-ref nil :read-only t)
  (memory-ref nil :read-only t)
  (root-node nil :read-only t)
  (head-cell nil :read-only t)
  (projection-policy nil :read-only t)
  (metadata nil :read-only t)
  (lifecycle :created :read-only t))

(defun world-id (world) (%world-id world))
(defun world-graph-ref (world) (%world-graph-ref world))
(defun world-memory-ref (world) (%world-memory-ref world))
(defun world-root-node (world) (%world-root-node world))
(defun world-head-node (world) (car (%world-head-cell world)))
(defun world-projection-policy (world) (copy-tree (%world-projection-policy world)))
(defun world-metadata (world) (copy-tree (car (%world-metadata world))))
(defun world-lifecycle (world) (car (%world-lifecycle world)))

(defun %require-graph-node (graph node-id label)
  (unless (get-node graph node-id) (error "~A must exist in the canonical graph: ~S" label node-id)))

(defun make-world (id graph-ref memory-ref root-node head-node projection-policy &optional metadata)
  "Create a view over existing canonical objects.  ID uniqueness is enforced by REGISTRY."
  (unless (and id (not (and (stringp id) (zerop (length id)))))
    (error "A world requires a non-empty stable id."))
  (%require-graph-node graph-ref root-node "Root node")
  (%require-graph-node graph-ref head-node "Head node")
  (%make-world id graph-ref memory-ref root-node (list head-node)
               (copy-tree projection-policy) (list (copy-tree metadata)) (list :created)))

(defun fork-world (parent child-id)
  "Create an isolated child view.  The caller records ancestry in the Registry."
  (make-world child-id (world-graph-ref parent) (world-memory-ref parent)
              (world-root-node parent) (world-head-node parent)
              (world-projection-policy parent) (world-metadata parent)))

(defun replace-world-metadata! (world metadata)
  "Copy-on-write metadata replacement; graph and memory are never affected."
  (setf (car (%world-metadata world)) (copy-tree metadata)) world)

(defun %set-world-lifecycle! (world lifecycle)
  (setf (car (%world-lifecycle world)) lifecycle) world)

(defun kernel-commit-world! (world node)
  "The Kernel's visibility boundary: append to Graph, then publish World head."
  (unless (causal-node-p node) (error "A kernel commit requires a causal-node."))
  (when (get-node (world-graph-ref world) (causal-node-id node))
    (error "Committed node ids are immutable and cannot be reused: ~S" (causal-node-id node)))
  ;; This ordered pair is the sole R2.0-B head advancement operation.
  (add-node! (world-graph-ref world) node)
  (setf (car (%world-head-cell world)) (causal-node-id node))
  world)

(defun %policy-includes-evaluations-p (policy)
  (not (null (getf policy :include-evaluations))))

(defun replay-world (world)
  "Pure, deterministic execution state derived only from the constitutional replay input."
  (let* ((policy (world-projection-policy world))
         (prefill (build-prefill-state (world-graph-ref world) (world-memory-ref world)
                                       (world-head-node world)
                                       :include-evaluations (%policy-includes-evaluations-p policy))))
    (list :world-id (world-id world)
          :head-node (world-head-node world)
          :projection-policy policy
          :metadata (world-metadata world)
          ;; Prefill structures are implementation objects; the content address
          ;; is the canonical replay-visible representation.
          :prefill-hash (prefill-state-hash prefill))))
