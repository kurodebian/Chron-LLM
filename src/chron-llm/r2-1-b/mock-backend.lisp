(in-package :chron-llm/r2-1-b)


(defstruct mock-scenario
  "A deterministic mock inference scenario.

ID identifies the scenario, MATCHER is a future extensibility hook
for conditional matching (for example Golden Test matching), and
OBSERVATION contains the inference result returned by the backend."
  id
  matcher
  observation)


(defparameter *mock-scenarios* nil
  "Registry of registered mock inference scenarios.

The registry is maintained as a list of MOCK-SCENARIO instances.")


(defun clear-mock-scenarios ()
  "Clear all registered mock inference scenarios."
  (setf *mock-scenarios* nil))


(defun register-mock-scenario (id observation &key matcher)
  "Register or replace a mock inference scenario.

ID must be a keyword identifying the scenario.
OBSERVATION must be an inference-observation instance.
MATCHER is stored for future matching extensions. If omitted,
a matcher that always succeeds is registered."
  (let ((scenario
          (make-mock-scenario
           :id id
           :matcher (or matcher
                        (constantly t))
           :observation observation)))
    (setf *mock-scenarios*
          (cons scenario
                (remove id
                        *mock-scenarios*
                        :key #'mock-scenario-id
                        :test #'eq)))
    scenario))


(defun find-mock-scenario-by-id (id)
  "Find and return the mock scenario registered with ID.

Returns NIL when no matching scenario exists."
  (find id
        *mock-scenarios*
        :key #'mock-scenario-id
        :test #'eq))


(defgeneric execute-inference (backend provider config prompt)
  (:documentation
   "Execute a single inference request and return an inference-observation.

BACKEND identifies the execution backend.
PROVIDER identifies the inference provider.
CONFIG contains backend-specific configuration.
PROMPT is the final inference prompt text."))


(defmethod execute-inference ((backend (eql :mock))
                              provider
                              config
                              prompt)
  "Execute a deterministic mock inference.

The scenario is selected exclusively through :MOCK-SCENARIO-ID
in CONFIG. Missing or unknown scenario identifiers are treated as
errors to preserve deterministic test behavior."
  (declare (ignore provider prompt))

  (let ((scenario-id (getf config :mock-scenario-id)))
    (unless scenario-id
      (error "Mock inference requires :MOCK-SCENARIO-ID in CONFIG."))

    (let ((scenario (find-mock-scenario-by-id scenario-id)))
      (unless scenario
        (error "No mock inference scenario registered for ID: ~S."
               scenario-id))

      (mock-scenario-observation scenario))))