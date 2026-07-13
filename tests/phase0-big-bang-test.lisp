(defpackage :chron-llm/tests/phase0
  (:use :cl)
  (:import-from :chron-llm/r1
                #:make-counter-generator
                #:generate-causal-id)
  (:export #:run-phase0-big-bang-test))

(in-package :chron-llm/tests/phase0)

(defstruct test-mock-provider
  (input-sequence nil)
  (execution-log nil))

(defmethod chron-llm/r1:fetch-observation ((provider test-mock-provider) action)
  (push (chron-llm/r2-3-s:physical-action-type action)
        (test-mock-provider-execution-log provider))
  (let ((next-text (pop (test-mock-provider-input-sequence provider))))
    (chron-llm/r2-1-b:make-inference-observation
     :raw-text (or next-text "default-test-fact")
     :prompt-text nil
     :usage-tokens nil
     :token-count 0
     :finish-reason :stop
     :config '(:mode :test)
     :provider-metadata '(:provider :test-mock)
     :error-info nil)))

(defun run-phase0-big-bang-test ()
  (let* ((genesis (chron-llm/r2-3-s:make-world-state
                   :causal-id "genesis"
                   :parent-id nil
                   :status :running
                   :retry-count 0
                   :history nil
                   :context '(:phase :test :origin :genesis)))
         (provider (make-test-mock-provider :input-sequence '("hello" "world")))
         (generator (make-counter-generator))
         (current-world genesis)
         (obs (chron-llm/r2-1-b:make-bootstrap-observation)))

    (dotimes (i 2)
      ;; 確定された「4層統一パイプライン」のシークエンス
      (let* ((decision (chron-llm/r2-2-e:evaluate-observation current-world obs '(:policy :default)))
             (ops (chron-llm/r2-2-e:derive-ops decision current-world)))
        
        (multiple-value-bind (new-world action)
            (chron-llm/r2-3-s:scheduler-step current-world ops (generate-causal-id generator))
          
          ;; インバリアント検証
          (assert (string= (chron-llm/r2-3-s:world-state-causal-id current-world)
                           (chron-llm/r2-3-s:world-state-parent-id new-world)))
          (assert (eq (chron-llm/r2-3-s:physical-action-type action) :invoke-api))
          
          (setf current-world new-world)
          (setf obs (chron-llm/r1:fetch-observation provider action)))))

    ;; 最終インバリアント検証
    (assert (string= (chron-llm/r2-3-s:world-state-causal-id current-world) "node-2"))
    (assert (= (chron-llm/r2-3-s:world-state-retry-count current-world) 2))
    
    (format t "~&Phase 0 Big Bang verification passed.~%")
    t))