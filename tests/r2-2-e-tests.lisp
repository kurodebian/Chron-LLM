;;;; tests/r2-2-e-tests.lisp

(defpackage :chron-llm/r2-2-e-tests
  (:use :cl)
  (:import-from :chron-llm/r2-2-e
                #:evaluate-observation
                #:derive-ops
                #:inference-decision-type)
  (:import-from :chron-llm/r2-1-b
                #:make-inference-observation)
  (:export
   #:run-r2-2-e-verification))


(in-package :chron-llm/r2-2-e-tests)


(defun %make-stop-observation ()
  "Create deterministic successful observation."
  (make-inference-observation
   :raw-text "ok"
   :prompt-text "test"
   :usage-tokens '(:input 1 :output 1)
   :token-count 1
   :finish-reason :stop
   :config nil
   :provider-metadata nil
   :error-info nil))


(defun %make-timeout-observation ()
  "Create deterministic timeout observation."
  (make-inference-observation
   :raw-text nil
   :prompt-text "timeout"
   :usage-tokens '(:input 1 :output 0)
   :token-count 0
   :finish-reason :timeout
   :config nil
   :provider-metadata nil
   :error-info '(:type :timeout
                 :message "timeout")))


(defun run-r2-2-e-verification ()
  "Run E-Tier verification suite for R2.2-E."

  ;; E1: Deterministic Decision
  (let* ((observation (%make-stop-observation))
         (policy '())
         (world-state '(:state 1))
         (decision-a
           (evaluate-observation
            world-state
            observation
            policy))
         (decision-b
           (evaluate-observation
            world-state
            observation
            policy)))

    (assert (eq (inference-decision-type decision-a)
                (inference-decision-type decision-b))))


  ;; E2: No Side Effects
  (let* ((world-state '(:counter 10))
         (before (copy-list world-state)))

    (evaluate-observation
     world-state
     (%make-stop-observation)
     nil)

    (assert (equal world-state before)))


  ;; E3: Error-as-Fact Handling
  (let* ((policy
           '(:timeout
             (:action :retry
              :params (:reason :temporary))))
         (decision
           (evaluate-observation
            nil
            (%make-timeout-observation)
            policy)))

    (assert (eq (inference-decision-type decision)
                :retry)))


  ;; E4: Policy Safety
  (let* ((policy nil)
         (observation
           (make-inference-observation
            :raw-text nil
            :prompt-text "unknown"
            :usage-tokens nil
            :token-count 0
            :finish-reason :error
            :config nil
            :provider-metadata nil
            :error-info '(:type :unknown-error)))
         (decision
           (evaluate-observation
            nil
            observation
            policy)))

    (assert (eq (inference-decision-type decision)
                :abort)))


  ;; E5: Replay Consistency
  (let* ((decision
           (evaluate-observation
            nil
            (%make-stop-observation)
            nil))
         (ops-a
           (derive-ops decision nil))
         (ops-b
           (derive-ops decision nil)))

    (assert (equal ops-a ops-b)))


  (format t "E-Tier verification passed.~%")
  t)