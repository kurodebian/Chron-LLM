(in-package :chron-llm/r2-1-b)


(defun %make-test-observation (&key
                                 raw-text
                                 prompt-text
                                 usage-tokens
                                 token-count
                                 finish-reason
                                 config
                                 provider-metadata
                                 error-info)
  "Create a test inference-observation with validated primitive data."
  (make-inference-observation
   :raw-text raw-text
   :prompt-text prompt-text
   :usage-tokens usage-tokens
   :token-count token-count
   :finish-reason finish-reason
   :config config
   :provider-metadata provider-metadata
   :error-info error-info))


(defun %register-basic-success-scenario ()
  "Register a deterministic successful mock inference scenario."
  (register-mock-scenario
   :mock-success-basic
   (%make-test-observation
    :raw-text "mock-success-response"
    :prompt-text "test prompt"
    :usage-tokens '(:input 10 :output 5)
    :token-count 5
    :finish-reason :stop
    :config '(:temperature 0.0)
    :provider-metadata '(:model "mock-model")
    :error-info nil)))


(defun %register-timeout-scenario ()
  "Register a deterministic timeout mock inference scenario."
  (register-mock-scenario
   :mock-openai-timeout
   (%make-test-observation
    :raw-text nil
    :prompt-text "timeout prompt"
    :usage-tokens '(:input 12 :output 0)
    :token-count 0
    :finish-reason :timeout
    :config '(:timeout 30)
    :provider-metadata '(:provider "mock-openai")
    :error-info '(:type :timeout
                  :message "Provider request timeout."))))


(defun run-r2-1-b-verification ()
  "Run R2.1-B Backend ABI verification tests D1-D6.

Each verification case resets the mock registry before execution.
Signals an error immediately if any invariant is violated."
  ;; D1: Single Attempt (Mock Success)
  (clear-mock-scenarios)
  (%register-basic-success-scenario)
  (let ((obs (execute-inference
              :mock
              :ignored-provider
              '(:mock-scenario-id :mock-success-basic)
              "hello")))
    (assert obs)
    (assert (eq (inference-observation-finish-reason obs)
                :stop))
    (assert (string= (inference-observation-raw-text obs)
                     "mock-success-response")))


  ;; D2: Error-as-Fact (Mock Error)
  (clear-mock-scenarios)
  (%register-timeout-scenario)
  (let ((obs (execute-inference
              :mock
              :openai
              '(:mock-scenario-id :mock-openai-timeout)
              "timeout test")))
    (assert (eq (inference-observation-finish-reason obs)
                :timeout))
    (assert (getf (inference-observation-error-info obs)
                  :message)))


  ;; D3: No Partial Mutation
  (clear-mock-scenarios)
  (%register-basic-success-scenario)
  (let* ((obs (execute-inference
               :mock
               nil
               '(:mock-scenario-id :mock-success-basic)
               "mutation test"))
         (config-copy (inference-observation-config obs)))
    (setf (getf config-copy :temperature) 99.0)
    (assert (= (getf (inference-observation-config obs)
                     :temperature)
               0.0)))


  ;; D4: Observation Immutability
  (clear-mock-scenarios)
  (%register-basic-success-scenario)
  (let* ((obs (execute-inference
               :mock
               nil
               '(:mock-scenario-id :mock-success-basic)
               "immutability test"))
         (metadata-a (inference-observation-provider-metadata obs))
         (metadata-b (inference-observation-provider-metadata obs)))
    (setf (getf metadata-a :model) "changed")
    (assert (string= (getf metadata-b :model)
                     "mock-model"))
    (assert (string= (getf (inference-observation-provider-metadata obs)
                           :model)
                     "mock-model")))


  ;; D5: Deterministic Replay (ID Matching)
  (clear-mock-scenarios)
  (%register-basic-success-scenario)
  (let ((obs-a (execute-inference
                :mock
                :provider-a
                '(:mock-scenario-id :mock-success-basic)
                "context-a"))
        (obs-b (execute-inference
                :mock
                :provider-b
                '(:mock-scenario-id :mock-success-basic)
                "context-b")))
    (assert (string= (inference-observation-raw-text obs-a)
                     (inference-observation-raw-text obs-b)))
    (assert (eq (inference-observation-finish-reason obs-a)
                (inference-observation-finish-reason obs-b))))


  ;; D6: Provider Abstraction Independence
  (clear-mock-scenarios)
  (%register-basic-success-scenario)
  (let ((obs-a (execute-inference
                :mock
                :provider-one
                '(:mock-scenario-id :mock-success-basic)
                "same prompt"))
        (obs-b (execute-inference
                :mock
                '(:some arbitrary provider object)
                '(:mock-scenario-id :mock-success-basic)
                "same prompt")))
    (assert (string= (inference-observation-raw-text obs-a)
                     (inference-observation-raw-text obs-b))))

  (format t "D-Tier verification passed.~%")
  t)