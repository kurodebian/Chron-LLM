;;;; src/chron-llm/r2-2-e/evaluator.lisp

(in-package :chron-llm/r2-2-e)

(defstruct inference-decision
  type
  payload
  reason
  finish-reason
  error-info
  policy
  strategy)


(defun get-strategy (reason policy)
  "Retrieve a strategy from POLICY for REASON.

POLICY is treated as external data.
If no strategy is defined, return a safe abort strategy."
  (or (getf policy reason)
      '(:action :abort
        :params nil)))


(defun evaluate-observation (world-state observation policy)
  "Pure Observation -> Decision v0 transformation."
  (declare (ignore world-state policy))

  (make-inference-decision
   :type :continue
   :payload
   `(:fact
     ,(chron-llm/r2-1-b:inference-observation-raw-text observation))
   :reason
   (chron-llm/r2-1-b:inference-observation-finish-reason observation)
   :finish-reason
   (chron-llm/r2-1-b:inference-observation-finish-reason observation)
   :error-info
   (chron-llm/r2-1-b:inference-observation-error-info observation)
   :policy
   policy
   :strategy
   '(:mode :bypass)))



(defun derive-ops (decision world-state)
  "Convert an inference decision into executable operations.

   WORLD-STATE is read-only and never modified.
   Returns a deterministic command list."
  (declare (ignore world-state))

  (case (inference-decision-type decision)

    (:continue
     ;; Phase 0:
     ;; Decision-level continuation is lowered to scheduler-level retry.
     ;; Scheduler retry means "advance causal loop via external action",
     ;; not inference retry semantics.
     (list :op :retry
           :payload
           (inference-decision-payload decision)))

    (:retry
     (list :op :retry
           :payload
           (inference-decision-payload decision)))

    (:abort
     (list :op :abort
           :reason
           (inference-decision-reason decision)))

(:optimize
 (list :op :optimize
       :payload
       (inference-decision-payload decision)))


    (otherwise
     '(:op :abort
       :reason :unknown-decision))))