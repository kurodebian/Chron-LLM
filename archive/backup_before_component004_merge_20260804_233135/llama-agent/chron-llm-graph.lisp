(in-package :chron-llm)

;;; ============================================================
;;; Graph Projection Service
;;; ============================================================
;;; Responsibility:
;;;   WAL -> Graph Projection
;;;
;;; This layer DOES NOT:
;;;   - validate events
;;;   - perform immune checks
;;;   - build prompts
;;;   - manage history summaries
;;;
;;; It ONLY reconstructs a projection from committed WAL events.
;;; ============================================================

(defun rebuild-graph-from-wal (wal)
  "Rebuild Graph Projection from committed WAL."
  (lift-to-graph wal))

;;; ============================================================
;;; Projection
;;; ============================================================

(defun lift-to-graph (wal)

  (let ((graph                  (make-causal-graph))
        (last-temporal-id       nil)
        (last-healthy-causal-id (make-hash-table))
        (global-last-healthy-id nil))

    (loop for ev across (wal-storage wal)
          do

            (let* ((node
                    (add-node-to-graph graph ev))

                   (node-id
                    (causal-node-id node)))

              ;; ------------------------------------------------
              ;; Temporal Edge
              ;; ------------------------------------------------

              (when last-temporal-id
                (add-edge
                 graph
                 :temporal
                 last-temporal-id
                 node-id))

              ;; ------------------------------------------------
              ;; Causal Edge
              ;; ------------------------------------------------

              (let ((parent-id
                     (find-parent-node-id
                      (ev-causal-id ev)
                      last-healthy-causal-id
                      global-last-healthy-id)))

                (when parent-id
                  (add-causal-edge
                   graph
                   parent-id
                   node-id)))

              ;; ------------------------------------------------
              ;; Healthy Table
              ;; ------------------------------------------------

              (unless (eq (causal-node-class node) :fault)

                (setf (gethash
                       (ev-causal-id ev)
                       last-healthy-causal-id)
                      node-id)

                (setf global-last-healthy-id
                      node-id))

              ;; ------------------------------------------------
              ;; Temporal Cursor
              ;; ------------------------------------------------

              (setf last-temporal-id
                    node-id)))

    ;; O(1) lookup table

    (setf (causal-graph-latest-healthy graph)
          last-healthy-causal-id)

    graph))

;;; ============================================================
;;; Parent Lookup
;;; ============================================================

(defun find-parent-node-id (cid table fallback)

  (multiple-value-bind (value found)

      (gethash cid table)

    (if found
        value
        fallback)))

(defun get-parent-node-id (graph node-id)

  (gethash node-id
           (causal-graph-causal-parents graph)))

;;; ============================================================
;;; Node Construction
;;; ============================================================

(defun add-node-to-graph (graph ev)

  ;; Validation is performed before WAL commit.
  ;; Projection assumes committed events are valid.

  (let* ((node-id
          (ev-node-id ev))

         (class
          (determine-node-class
           (ev-kind ev)))

         (node
          (make-instance
           'causal-node

           :id node-id
           :event ev
           :class class
           :clock (ev-clock ev)
           :causal-id (ev-causal-id ev))))

    (setf (gethash node-id
                   (causal-graph-nodes graph))
          node)

    node))

;;; ============================================================
;;; Edge Operations
;;; ============================================================

(defun add-edge (graph kind from to)

  (vector-push-extend

   (make-edge
    :kind kind
    :from from
    :to to)

   (causal-graph-edges graph)))

(defun add-causal-edge (graph from to)

  (add-edge graph
            :causal
            from
            to)

  (setf (gethash to
                 (causal-graph-causal-parents graph))
        from))

;;; ============================================================
;;; History Query
;;; ============================================================

(defun graph-history (graph world-id)
  "Current history query.
Future versions will move this function into History Service."

  (let ((latest-node-id
         (gethash world-id
                  (causal-graph-latest-healthy graph))))

    (unless latest-node-id
      (return-from graph-history nil))

    (let ((history nil)
          (current-id latest-node-id))

      (loop while current-id
            do

              (let ((node
                     (gethash current-id
                              (causal-graph-nodes graph))))

                (when (and node
                           (eq (causal-node-class node)
                               :dialogue))
                  (push node history))

                (setf current-id
                      (get-parent-node-id
                       graph
                       current-id))))

      history)))

;;; ============================================================
;;; Backward Compatibility
;;; ============================================================

(defun clean-history (graph world-id)
  (graph-history graph world-id))