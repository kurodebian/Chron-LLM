(in-package :cl-user)

(defpackage :chron-llm/r2-3-s-tests
  (:use :cl)
  (:import-from :chron-llm/r2-3-s
                #:make-world-state
                #:copy-world-state
                #:world-state-causal-id
                #:world-state-parent-id
                #:world-state-status
                #:world-state-retry-count
                #:world-state-history
                #:world-state-context
                #:make-physical-action
                #:physical-action-type
                #:physical-action-payload
                #:scheduler-step)
  (:export #:run-r2-3-s-verification))

(in-package :chron-llm/r2-3-s-tests)

(defun %make-genesis-world ()
  "Genesis: The zero-point of the worldline. No semantic info."
  (make-world-state
   :causal-id "genesis"
   :parent-id nil
   :status :running
   :retry-count 0
   :history nil
   :context '(:phase :r2-3-s :origin :genesis)))

(defun run-r2-3-s-verification ()
  "Run S-Tier verification suite for R2.3-S."

  ;; S1: Immutable State (Side-effect free)
  (let* ((world (%make-genesis-world))
         (before (copy-world-state world)))
    (multiple-value-bind (new-world action)
        (scheduler-step world '(:op :retry) "child")
      (declare (ignore new-world action))
      (assert (equalp world before))))

  ;; S2: WAL Append & Structural Sharing
  (let* ((world (%make-genesis-world))
         (old-history (world-state-history world))
         (ops '(:op :retry :payload (:request 1))))
    (multiple-value-bind (new-world action)
        (scheduler-step world ops "child")
      (declare (ignore action))
      ;; Verify new history head is ops
      (assert (equal ops (first (world-state-history new-world))))
      ;; Verify O(1) structural sharing (the physical backbone of the WAL)
      (assert (eq old-history (cdr (world-state-history new-world))))))

  ;; S3: Causal-ID Branching
  (let ((world (%make-genesis-world)))
    (multiple-value-bind (new-world action)
        (scheduler-step world '(:op :retry) "child-id")
      (declare (ignore action))
      (assert (string= "child-id" (world-state-causal-id new-world)))
      (assert (string= "genesis" (world-state-parent-id new-world)))))

  ;; S4: State Transition & Physical Action
  (let ((world (%make-genesis-world)))
    ;; Retry check
    (multiple-value-bind (w-retry a-retry)
        (scheduler-step world '(:op :retry) "c1")
      (assert (= 1 (world-state-retry-count w-retry)))
      (assert (eq :invoke-api (physical-action-type a-retry))))
    ;; Abort check
    (multiple-value-bind (w-abort a-abort)
        (scheduler-step world '(:op :abort) "c2")
      (assert (eq :halted (world-state-status w-abort)))
      (assert (eq :halt (physical-action-type a-abort)))))

  (format t "S-Tier verification passed.~%")
  t)
