(defpackage :experiment
  (:use :cl)
  (:export
   #:make-3cluster-graph
   #:node-id #:node-role
   #:edge-from #:edge-to #:edge-relation #:edge-strength
   #:graph-nodes #:graph-edges
   ;; ← ここを追加
   #:compute-sccs
   #:find-recurrent-cycle
   #:find-cycle
   #:build-basin-structure
   #:basin
   #:rollout*
   #:next-event
   #:find-attractor
   #:build-basin-map))


(in-package :experiment)

(defstruct node id role)
(defstruct edge from to relation strength)
(defstruct graph nodes edges)

(defun make-3cluster-graph ()
  (let* ((nodes (list
                 (make-node :id :a1 :role :reply)
                 (make-node :id :a2 :role :reply)
                 (make-node :id :a3 :role :reply)
                 (make-node :id :b1 :role :temporal)
                 (make-node :id :b2 :role :temporal)
                 (make-node :id :b3 :role :temporal)
                 (make-node :id :c1 :role :bridge)
                 (make-node :id :c2 :role :bridge)))

         (edges (list
                 ;; A cluster
                 (make-edge :from :a1 :to :a2 :relation :reply :strength 0.9)
                 (make-edge :from :a2 :to :a3 :relation :reply :strength 0.9)
                 (make-edge :from :a3 :to :a1 :relation :reply :strength 0.9)

                 ;; B cluster
                 (make-edge :from :b1 :to :b2 :relation :temporal :strength 0.3)
                 (make-edge :from :b2 :to :b3 :relation :temporal :strength 0.3)
                 (make-edge :from :b3 :to :b1 :relation :temporal :strength 0.3)

                 ;; C bridge
                 (make-edge :from :c1 :to :a1 :relation :reply :strength 0.6)
                 (make-edge :from :c1 :to :b1 :relation :temporal :strength 0.4)
                 (make-edge :from :c2 :to :a2 :relation :reply :strength 0.4)
                 (make-edge :from :c2 :to :b2 :relation :temporal :strength 0.6))))

    (make-graph :nodes nodes :edges edges)))
