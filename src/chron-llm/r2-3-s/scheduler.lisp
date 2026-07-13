(in-package :chron-llm/r2-3-s)

(defstruct (world-state
            (:copier copy-world-state))
  "Persistent representation of a causal worldline state.
Immutable. Transition creates new state objects."
  causal-id
  parent-id
  status
  retry-count
  history
  context)

(defstruct physical-action
  "Pure data representation of a physical execution request."
  type
  payload)

(defun scheduler-step (world-state ops new-causal-id)
  "Advance WORLD-STATE according to OPS.
Returns two values: new world-state, physical-action.
Original WORLD-STATE remains untouched."
  (let* ((new-status (world-state-status world-state))
         (new-retry-count (world-state-retry-count world-state))
         (action nil))

    (cond
      ((and (listp ops) (eq (getf ops :op) :retry))
       (setf new-retry-count (1+ new-retry-count)
             action (make-physical-action :type :invoke-api :payload (getf ops :payload))))

      ((and (listp ops) (eq (getf ops :op) :abort))
       (setf new-status :halted
             action (make-physical-action :type :halt :payload nil)))

      (t
       (setf action (make-physical-action :type :halt :payload nil))))

    (values
     (make-world-state
      :causal-id new-causal-id
      :parent-id (world-state-causal-id world-state)
      :status new-status
      :retry-count new-retry-count
      ;; WAL: Structural sharing via cons ensures O(1) history update
      :history (cons ops (world-state-history world-state))
      ;; Context: Deep copy to ensure isolation of immutable state
      :context (copy-list (world-state-context world-state)))
     action)))