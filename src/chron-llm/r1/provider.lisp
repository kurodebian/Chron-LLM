(in-package :cl-user)

(defpackage :chron-llm/r1
  (:use :cl)
  (:import-from :chron-llm/r2-1-b
                #:make-inference-observation)
  (:import-from :chron-llm/r2-3-s
                #:physical-action-type)
  (:export
   #:cli-provider
   #:make-cli-provider
   #:fetch-observation
   #:counter-generator
   #:make-counter-generator
   #:generate-causal-id))


(in-package :chron-llm/r1)


(defstruct cli-provider)


(defmethod fetch-observation ((provider cli-provider) action)
  (declare (ignore provider))

  (format t "~&[R1-CLI] Action Executed: ~a~%"
          (physical-action-type action))

  (format t "[R1-CLI] Input next raw-text: ")
  (finish-output)

  (make-inference-observation
   :raw-text (read-line)
   :prompt-text nil
   :usage-tokens nil
   :token-count 0
   :finish-reason :stop
   :config '(:mode :interactive)
   :provider-metadata '(:provider :cli)
   :error-info nil))


(defstruct counter-generator
  (counter 0))


(defgeneric generate-causal-id (generator))


(defmethod generate-causal-id ((generator counter-generator))
  (format nil
          "node-~d"
          (incf (counter-generator-counter generator))))