(in-package :chron-llm/r2-1-b)

(defstruct (inference-observation
    (:constructor %make-inference-observation
        (raw-text
         prompt-text
         usage-tokens
         token-count
         finish-reason
         config
         provider-metadata
         error-info))
    (:conc-name %inference-observation-)
    (:type vector))
  "Immutable, encapsulated representation of a single inference event.
   Stored as a primitive vector to erase object identity."
  raw-text
  prompt-text
  usage-tokens
  token-count
  finish-reason
  config
  provider-metadata
  error-info)


(defun make-inference-observation (&key
                                     raw-text
                                     prompt-text
                                     usage-tokens
                                     token-count
                                     finish-reason
                                     config
                                     provider-metadata
                                     error-info)
  "Validate primitive-tree fields and construct a new inference-observation.

   Only primitive values and pure primitive trees are accepted for
   structured fields. The resulting object contains no external object
   identity."
  (chron-r2-0-c::%require-primitive-tree usage-tokens :usage-tokens)
  (chron-r2-0-c::%require-primitive-tree config :config)
  (chron-r2-0-c::%require-primitive-tree provider-metadata :provider-metadata)
  (chron-r2-0-c::%require-primitive-tree error-info :error-info)

  (%make-inference-observation
   raw-text
   prompt-text
   usage-tokens
   token-count
   finish-reason
   config
   provider-metadata
   error-info))


(defun inference-observation-raw-text (obs)
  "Return the raw response text stored in OBS."
  (%inference-observation-raw-text obs))


(defun inference-observation-prompt-text (obs)
  "Return the final prompt text stored in OBS."
  (%inference-observation-prompt-text obs))


(defun inference-observation-usage-tokens (obs)
  "Return a defensive deep copy of the usage token information stored in OBS."
  (chron-r2-0-c::%copy-primitive-tree
   (%inference-observation-usage-tokens obs)))


(defun inference-observation-token-count (obs)
  "Return the output token count stored in OBS."
  (%inference-observation-token-count obs))


(defun inference-observation-finish-reason (obs)
  "Return the inference completion reason stored in OBS."
  (%inference-observation-finish-reason obs))


(defun inference-observation-config (obs)
  "Return a defensive deep copy of the inference configuration stored in OBS."
  (chron-r2-0-c::%copy-primitive-tree
   (%inference-observation-config obs)))


(defun inference-observation-provider-metadata (obs)
  "Return a defensive deep copy of provider metadata stored in OBS."
  (chron-r2-0-c::%copy-primitive-tree
   (%inference-observation-provider-metadata obs)))


(defun inference-observation-error-info (obs)
  "Return a defensive deep copy of error information stored in OBS."
  (chron-r2-0-c::%copy-primitive-tree
   (%inference-observation-error-info obs)))
