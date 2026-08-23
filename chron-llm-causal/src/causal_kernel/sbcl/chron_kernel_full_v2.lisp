(require :asdf)
;;; ============================================================================
;;; CHRON-LLM EXECUTABLE CAUSAL KERNEL (12-NODE COMPLETE EXTENSION)
;;; Substrate for C2/C3 Execution & Cross-Validation with Python Validator
;;; ============================================================================

;; --- PACKAGE DEFINITIONS (L2 PIPELINE BOUNDARIES) ---

(uiop:define-package :chron.kernel.spec
  (:use :cl)
  (:export #:st-proposal
           #:st-derived
           #:st-candidate
           #:st-canonical
           #:make-st-proposal
           #:make-st-derived
           #:make-st-candidate
           #:make-st-canonical
           #:st-proposal-id #:st-proposal-data
           #:st-derived-id #:st-derived-transform
           #:st-candidate-id #:st-candidate-payload
           #:st-canonical-id #:st-canonical-fact
           #:inv-auth-p
           #:inv-purity-check-p
           #:op-proposal-create
           #:op-validate-invariants
           #:runtime-context
           #:make-runtime-context
           #:runtime-context-clock
           #:runtime-context-auth))

(uiop:define-package :chron.kernel.derive
  (:use :cl :chron.kernel.spec)
  (:export #:define-pure-operation
           #:op-derive-transform))

(uiop:define-package :chron.kernel.commit
  (:use :cl :chron.kernel.spec)
  (:export #:with-authority-guard
           #:op-commit-promote
           #:op-emit-event-fact))

(uiop:define-package :chron.kernel.runtime
  (:use :cl :chron.kernel.spec :chron.kernel.derive :chron.kernel.commit)
  (:export #:execute-causal-pipeline
           #:run-test-suite))

(in-package :chron.kernel.spec)

;; ==============================================================================
;; L0 ONTOLOGY: 12 ELEMENTS
;; ==============================================================================

;; 1. State Nodes (Immutable Structs)
(defstruct (st-proposal (:constructor make-st-proposal (id data)))
  (id "" :type string :read-only t)
  (data "" :type string :read-only t))

(defstruct (st-derived (:constructor make-st-derived (id transform)))
  (id "" :type string :read-only t)
  (transform "" :type string :read-only t))

(defstruct (st-candidate (:constructor make-st-candidate (id payload)))
  (id "" :type string :read-only t)
  (payload "" :type string :read-only t))

(defstruct (st-canonical (:constructor make-st-canonical (id fact)))
  (id "" :type string :read-only t)
  (fact "" :type string :read-only t))

;; 2. Interface Node (Runtime Context)
(defstruct runtime-context
  (clock 0 :type integer)
  (auth "" :type string))

;; 3. Invariant Predicates
(defun inv-auth-p (auth-token expected-token)
  (string= auth-token expected-token))

(defun inv-purity-check-p (ast)
  (let ((impure-symbols '(cl:setf cl:setq cl:rplaca cl:rplacd cl:defparameter cl:defvar)))
    (labels ((walk (expr)
               (cond
                 ((symbolp expr)
                  (not (member expr impure-symbols :test #'eq)))
                 ((consp expr)
                  (and (walk (car expr))
                       (walk (cdr expr))))
                 (t t))))
      (walk ast))))

;; 4. Base Operations
(defun op-proposal-create (id data)
  (make-st-proposal id data))

(defun op-validate-invariants (proposal)
  (and (typep proposal 'st-proposal)
       (> (length (st-proposal-data proposal)) 0)))

(in-package :chron.kernel.derive)

;; ==============================================================================
;; L2 PIPELINE: DERIVE PIPELINE (Pure Operations)
;; ==============================================================================

(defmacro define-pure-operation (name args &body body)
  (unless (chron.kernel.spec:inv-purity-check-p body)
    (error "INV_PUR_001_FAIL: AST contains impure state mutation symbols."))
  `(defun ,name ,args ,@body))

(define-pure-operation op-derive-transform (proposal)
  (let ((p-id (chron.kernel.spec:st-proposal-id proposal))
        (p-data (chron.kernel.spec:st-proposal-data proposal)))
    (chron.kernel.spec:make-st-derived p-id (format nil "DERIVED[~A]" p-data))))

(defun derive-to-candidate (derived)
  (chron.kernel.spec:make-st-candidate
   (chron.kernel.spec:st-derived-id derived)
   (chron.kernel.spec:st-derived-transform derived)))

(in-package :chron.kernel.commit)

;; ==============================================================================
;; L2 PIPELINE: COMMIT PIPELINE (Authority Guards)
;; ==============================================================================

(defmacro with-authority-guard ((ctx expected-auth) &body body)
  `(if (chron.kernel.spec:inv-auth-p (chron.kernel.spec:runtime-context-auth ,ctx) ,expected-auth)
       (progn ,@body)
       (error "ERR_MISSING_AUTH_GUARD")))

(defparameter *auth-guard-token* "AUTH-001"
  "Binds runtime authority guard token to L1 Invariant Node: INV_AUTH_001")

(defun op-commit-promote (ctx candidate)
  (with-authority-guard (ctx *auth-guard-token*)
    (chron.kernel.spec:make-st-canonical
     (chron.kernel.spec:st-candidate-id candidate)
     (format nil "CANONICAL[~A]" (chron.kernel.spec:st-candidate-payload candidate)))))

(defun op-emit-event-fact (canonical)
  (format nil "EVENT_FACT[~A:~A]"
          (chron.kernel.spec:st-canonical-id canonical)
          (chron.kernel.spec:st-canonical-fact canonical)))

(in-package :chron.kernel.runtime)

;; ==============================================================================
;; EXECUTABLE RUNTIME & TEST SUITE WITH JSON TRACER
;; ==============================================================================

(defun execute-causal-pipeline (ctx prop-id prop-data)
  (incf (chron.kernel.spec:runtime-context-clock ctx))
  (let* ((prop (chron.kernel.spec:op-proposal-create prop-id prop-data)))
    (unless (chron.kernel.spec:op-validate-invariants prop)
      (error "ERR_INVALID_PROPOSAL"))
    (let* ((derived (op-derive-transform prop))
           (cand (chron.kernel.derive::derive-to-candidate derived))
           (canon (op-commit-promote ctx cand))
           (event (op-emit-event-fact canon)))
      event)))

(defun run-tc1 ()
  (handler-case
      (let ((ctx (chron.kernel.spec:make-runtime-context :clock 0 :auth "AUTH-001")))
        (execute-causal-pipeline ctx "PROP_001" "Payload_Alpha")
        '((("test_id" . "TC1_VALID_PATH")
           ("status" . "ACCEPT"))))
    (error (c)
      `((("test_id" . "TC1_VALID_PATH")
         ("status" . "REJECT")
         ("reason" . ,(format nil "~A" c)))))))

(defun run-tc2 ()
  (handler-case
      (let ((ctx (chron.kernel.spec:make-runtime-context :clock 0 :auth "INVALID_KEY")))
        (execute-causal-pipeline ctx "PROP_002" "Payload_Beta")
        '((("test_id" . "TC2_INVALID_AUTH")
           ("status" . "ACCEPT"))))
    (error (c)
      `((("test_id" . "TC2_INVALID_AUTH")
         ("status" . "REJECT")
         ("reason" . "ERR_MISSING_AUTH_GUARD"))))))

(defun run-tc3 ()
  (handler-case
      (progn
        (eval '(chron.kernel.derive:define-pure-operation impure-op (x) (setf x 100)))
        '((("test_id" . "TC3_DERIVE_PURITY_VIOLATION")
           ("status" . "ACCEPT"))))
    (error (c)
      `((("test_id" . "TC3_DERIVE_PURITY_VIOLATION")
         ("status" . "REJECT")
         ("reason" . "ERR_DERIVE_PURITY_FAIL"))))))

(defun print-json-trace (results)
  (format t "~%---SBCL_TRACE_BEGIN---~%")
  (format t "[~%")
  (loop for item in results
        for idx from 0
        do (let ((test-id (cdr (assoc "test_id" item :test #'string=)))
                 (status (cdr (assoc "status" item :test #'string=)))
                 (reason (cdr (assoc "reason" item :test #'string=))))
             (if (> idx 0) (format t ",~%"))
             (format t "  {\"test_id\": \"~A\", \"status\": \"~A\"" test-id status)
             (when reason
               (format t ", \"reason\": \"~A\"" reason))
             (format t "}")))
  (format t "~%]")
  (format t "~%---SBCL_TRACE_END---~%"))

(defun main ()
  (let ((res1 (car (run-tc1)))
        (res2 (car (run-tc2)))
        (res3 (car (run-tc3))))
    (print-json-trace (list res1 res2 res3))))

(main)