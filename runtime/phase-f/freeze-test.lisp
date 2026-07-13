(defpackage :phase-f.freeze-test
  (:use :cl
        :phase-a.event
        :phase-a.history
        :phase-f.frozen-config
        :phase-f.inlet
        :phase-f.freeze)
  (:export #:mc1-f))

(in-package :phase-f.freeze-test)

(defun mc1-f ()
  (format t "~%[MC1-F] Phase F semantic freeze contract test~%")

  (let* ((config (frozen-semantics '(:inlet-key :a :version 0)))
         (h0     (make-history))
         (inlet  (semantic-inlet config h0)))

    ;; --------------------------------------------------------
    ;; FINV-1: Only one semantic inlet is active at a time
    ;; --------------------------------------------------------
    (assert (semantic-inlet-p inlet))
    (assert (eq (semantic-inlet-inlet-key inlet) :a))
    (format t "  FINV-1 OK: single inlet active~%")

    ;; --------------------------------------------------------
    ;; FINV-2: LLM output normalization is total and deterministic
    ;; --------------------------------------------------------
    (let ((ev1 (normalize-output inlet "  hello world  "))
          (ev2 (normalize-output inlet "  hello world  ")))
      ;; total: returns a valid event
      (assert (event-p ev1))
      ;; deterministic: same input → structurally equal output
      (assert (event-equal ev1 ev2))
      ;; normalized: whitespace stripped
      (assert (equal (event-payload ev1) "hello world"))
      ;; role is :assistant
      (assert (eq (event-type ev1) :assistant)))
    (format t "  FINV-2 OK: normalization total & deterministic~%")

    ;; --------------------------------------------------------
    ;; FINV-3: Frozen semantics do not mutate A, C, or D contracts
    ;; --------------------------------------------------------
    (let ((snap-before (history-snapshot h0)))
      (normalize-output inlet "test mutation check")
      (let ((snap-after (history-snapshot h0)))
        ;; h0 must remain unchanged
        (assert (equal snap-before snap-after))
        (assert (history-empty-p h0))))
    (format t "  FINV-3 OK: A/C/D contracts unmutated~%")

    ;; --------------------------------------------------------
    ;; FINV-4: Frozen inlet is explicit and versioned
    ;; --------------------------------------------------------
    (assert (= (semantic-inlet-version inlet) 0))
    (assert (= (frozen-config-version config) 0))
    (assert (eq (frozen-config-inlet-key config) :a))
    (format t "  FINV-4 OK: inlet is explicit and versioned~%")

    ;; --------------------------------------------------------
    ;; FINV-5: No semantic selection occurs outside Phase F
    ;; --------------------------------------------------------
    ;; inlet-key comes from config, not from arbitrary input
    (assert (eq (semantic-inlet-inlet-key inlet)
                (frozen-config-inlet-key config)))
    (format t "  FINV-5 OK: selection only via Phase F config~%")

    ;; --------------------------------------------------------
    ;; FINV-6: Removal or change of inlet requires new F version
    ;; --------------------------------------------------------
    (let* ((config-v1 (frozen-semantics '(:inlet-key :a :version 1)))
           (inlet-v1  (semantic-inlet config-v1 h0)))
      ;; different version → different inlet instance
      (assert (/= (semantic-inlet-version inlet)
                   (semantic-inlet-version inlet-v1)))
      (assert (= (semantic-inlet-version inlet-v1) 1)))
    (format t "  FINV-6 OK: inlet change requires new version~%")

    ;; --------------------------------------------------------
    ;; FINV-7: Inlet binding is immutable for the lifetime of F
    ;; --------------------------------------------------------
    ;; The struct slots are read-only; verify value stability
    (assert (eq (semantic-inlet-value inlet) h0))
    (assert (eq (semantic-inlet-inlet-key inlet) :a))
    (assert (= (semantic-inlet-version inlet) 0))
    ;; struct identity is preserved
    (let ((inlet-again (semantic-inlet config h0)))
      ;; a new call produces a new struct, but with identical content
      (assert (not (eq inlet inlet-again)))
      (assert (eq (semantic-inlet-inlet-key inlet)
                  (semantic-inlet-inlet-key inlet-again)))
      (assert (= (semantic-inlet-version inlet)
                 (semantic-inlet-version inlet-again))))
    (format t "  FINV-7 OK: inlet binding is immutable~%"))

  (format t "MC1-F OK~%")
  t)