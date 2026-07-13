(defpackage :phase-e.analyze
  (:use :cl
        :phase-d.graph
        :phase-d.edge)
  (:export
   #:observation
   #:observation-p
   #:observation-total
   #:observation-metrics
   #:analyze-graph
   #:graph-summary))

(in-package :phase-e.analyze)

;; ------------------------------------------------------------
;; Phase E Observation
;;
;; Pure structural observation over Graph.
;;
;; Guarantees:
;;   - deterministic
;;   - side-effect-free
;;   - graph is never modified
;;   - no semantic interpretation
;;
;; Observation is an immutable value object.
;;
;; METRICS is an implementation-defined property list containing
;; extensible structural measurements. New metrics MAY be added
;; without changing the Observation ABI.
;; ------------------------------------------------------------

(defstruct observation
  ;; Number of structural relations observed.
  (total 0 :type (integer 0 *))

  ;; Implementation-defined structural metrics.
  ;;
  ;; Current metrics:
  ;;   :reply-count
  ;;   :temporal-count
  ;;   :average-strength
  ;;
  ;; Future versions MAY additionally expose:
  ;;   :echo-score
  ;;   :drift-score
  ;;   :entropy
  ;;   :cycle-count
  ;;   :scc-count
  ;;
  ;; Existing keys MUST retain their meaning.
  (metrics nil :type list))

(defun analyze-graph (graph)
  "Observe structural properties of GRAPH.

Returns a deterministic, side-effect-free OBSERVATION.

The returned observation contains only structural facts and
performs no semantic interpretation."

  (let* ((edges (graph-edges graph))
         (total (length edges))
         (reply-count 0)
         (temporal-count 0)
         (average-strength 0.0))

    (dolist (edge edges)
      (incf average-strength
            (edge-strength edge))

      (case (edge-relation edge)
        (:reply
         (incf reply-count))
        (:temporal
         (incf temporal-count))))

    (when (plusp total)
      (setf average-strength
            (/ average-strength total)))

    (make-observation
     :total total
     :metrics
     (list
      :reply-count reply-count
      :temporal-count temporal-count
      :average-strength average-strength))))

(defun graph-summary (graph)
  "Return a human-readable summary of a Phase E observation."

  (let* ((obs (analyze-graph graph))
         (metrics (observation-metrics obs)))

    (format nil
            "Graph Observation

total edges      : ~D
reply edges      : ~D
temporal edges   : ~D
average strength : ~,2F"
            (observation-total obs)
            (getf metrics :reply-count)
            (getf metrics :temporal-count)
            (getf metrics :average-strength))))
