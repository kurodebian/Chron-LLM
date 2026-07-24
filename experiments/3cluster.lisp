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
   #:build-basin-map
   #:basin
   #:rollout*
   #:find-attractor
   #:build-basin-structure)
  )

(in-package :experiment)

(defstruct node id role)
(defstruct edge from to relation strength)
(defstruct graph nodes edges)
(defstruct trajectory-path start-node steps path terminal-node detected-cycle attractor)
(defstruct event-selection current-node selected-edge strength alternatives)
(defstruct recurrent-cycle cycle-id nodes length frequency stability attractor-type)
(defstruct scc-component component-id nodes reachability is-attractor stable-dynamics)
(defstruct basin attractor nodes mass ratio coverage-area)

;; Cluster Structure（仕様書 v0.2 定義）
(defstruct cluster
  cluster-id      ; A / B / C など
  type            ; reply-cluster / temporal-cluster / bridge-cluster
  nodes           ; (list of node-id) 所属ノード
  connections     ; 他のクラスターへの遷移エッジ
  stability       ; クラスター安定性スコア
  )

;; Three-Cluster Graph（仕様書 v0.2 定義）
(defstruct three-cluster-graph
  cluster-a       ; (cluster) reply cluster(強い循環)
  cluster-b       ; (cluster) temporal cluster(弱い循環)
  cluster-c       ; (cluster) bridge cluster(A/B を接続)
  )

(defun make-cluster-a ()
  "Create reply cluster A with strong cyclic dynamics."
  (make-cluster
   :cluster-id :a
   :type :reply-cluster
   :nodes '(:a1 :a2 :a3)
   :connections '((:to :c1 :strength 0.6) (:to :c2 :strength 0.4))
   :stability 0.9))

(defun make-cluster-b ()
  "Create temporal cluster B with weak cyclic dynamics."
  (make-cluster
   :cluster-id :b
   :type :temporal-cluster
   :nodes '(:b1 :b2 :b3)
   :connections '((:to :c1 :strength 0.4) (:to :c2 :strength 0.6))
   :stability 0.3))

(defun make-cluster-c ()
  "Create bridge cluster C connecting A and B."
  (make-cluster
   :cluster-id :c
   :type :bridge-cluster
   :nodes '(:c1 :c2)
   :connections '((:to :a1 :strength 0.6) (:to :b1 :strength 0.4))
   :stability 0.5))

(defun make-3cluster-graph ()
  "Create a graph with three clusters: A (reply), B (temporal), and C (bridge)."
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

    (let ((graph (make-graph :nodes nodes :edges edges)))
      ;; three-cluster-graph も作成して返す
      (values graph
              (make-three-cluster-graph
               :cluster-a (make-cluster-a)
               :cluster-b (make-cluster-b)
               :cluster-c (make-cluster-c)))))
)
