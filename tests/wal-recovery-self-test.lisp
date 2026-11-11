;;;; tests/wal-recovery-self-test.lisp
;;;; Recovery-norm self-test for runtime/phase-d/wal.lisp.
;;;; Encodes ratified norms ADR-001/ADR-002/ADR-003 (RATIFIED_HUMAN 2026-11-11):
;;;;   N1 PREPARED is never resolved to ABORT at recovery start (IN_DOUBT retained)
;;;;   N2 partial tail is quarantined (preserved), not silently truncated away
;;;;   N3 COMMITTED rollforward applies; IN_DOUBT never canonical
;;;;   N4 recovery is idempotent for committed state and keeps IN_DOUBT pending

(in-package :chron.kernel.wal)

(defparameter *test-dir* (uiop:ensure-directory-pathname "/tmp/wal-self-test"))
(ensure-directories-exist *test-dir*)

(defun reset-dir ()
  (when (probe-file *test-dir*)
    (uiop:delete-directory-tree *test-dir* :validate t))
  (ensure-directories-exist *test-dir*))

(defun wal-path (name)
  (merge-pathnames name *test-dir*))

(defun file-bytes (path)
  (with-open-file (s path :element-type '(unsigned-byte 8) :direction :input)
    (let ((buf (make-array (file-length s) :element-type '(unsigned-byte 8))))
      (read-sequence buf s)
      buf)))

(defun file-len (path)
  (with-open-file (s path :element-type '(unsigned-byte 8) :direction :input)
    (file-length s)))

;; --- N1/N3: crash before commit -> IN_DOUBT retained, never canonical ---
(defun test-in-doubt-retention ()
  (reset-dir)
  (let* ((p (wal-path "crash.wal"))
         (fd (open-wal-file p))
         (applied 0))
    (write-prepare-record fd 1 10 1234 '(:node "A"))
    (close-wal-file fd)
    (let ((len-before (file-len p)))
      (multiple-value-bind (next-tx valid-off q-bytes q-path)
          (recover-from-wal p (lambda (sexp) (declare (ignore sexp)) (incf applied)))
        (assert (= next-tx 2))
        (assert (= q-bytes 0))
        (assert (not (probe-file q-path))))
      (let ((scan (scan-wal-file p)))
        ;; recovery did not resolve PREPARED -> tx stays :prepared, not :aborted
        (assert (eq (gethash 1 (wal-scan-result-tx-table scan)) :prepared))
        ;; IN_DOUBT never canonical: apply hook never called for prepared tx
        (assert (= applied 0))
        ;; PREPARED record preserved in the WAL (never deleted by recovery)
        (assert (>= (file-len p) len-before)))))
  t)

;; --- N2: partial tail quarantined (preserved), not lost ---
(defun test-tail-quarantine ()
  (reset-dir)
  (let* ((p (wal-path "tail.wal"))
         (fd (open-wal-file p))
         (applied 0)
         (garbage (make-array 13 :element-type '(unsigned-byte 8)
                              :initial-contents '(1 2 3 4 5 6 7 8 9 10 11 12 13))))
    (write-prepare-record fd 1 10 1234 '(:node "A"))
    (close-wal-file fd)
    ;; simulate torn tail: 13 garbage bytes appended after the last valid record
    (let ((gfd (sb-posix:open p (logior sb-posix:o-wronly sb-posix:o-append))))
      (sb-posix:write gfd (sb-sys:vector-sap garbage) 13)
      (sb-posix:close gfd))
    (recover-from-wal p (lambda (sexp) (declare (ignore sexp)) (incf applied)))
    (let ((q (wal-path "tail.wal.quarantine")))
      ;; partial tail preserved in quarantine, byte-exact
      (assert (probe-file q))
      (let ((qb (file-bytes q)))
        (assert (= (length qb) 13))
        (assert (equal (coerce qb 'list) '(1 2 3 4 5 6 7 8 9 10 11 12 13)))
        ;; main WAL normalized to valid offset; garbage bytes are NOT in the WAL
        (assert (not (search garbage (file-bytes p)))))))
  t)

;; --- N3/N4: committed rollforward; idempotent re-recovery ---
(defun test-rollforward-idempotent ()
  (reset-dir)
  (let* ((p (wal-path "roll.wal"))
         (fd (open-wal-file p))
         (applied 0))
    (write-prepare-record fd 2 20 4321 '(:node "B"))
    (write-commit-record fd 2 21)
    (close-wal-file fd)
    (recover-from-wal p (lambda (sexp) (declare (ignore sexp)) (incf applied)))
    (assert (= applied 1))
    ;; second recovery: committed tx re-derived from durable log (rollforward
    ;; re-derives Canonical from WAL; idempotent per recovery run)
    (recover-from-wal p (lambda (sexp) (declare (ignore sexp)) (incf applied)))
    (assert (= applied 2))
    (let ((scan (scan-wal-file p)))
      (assert (eq (gethash 2 (wal-scan-result-tx-table scan)) :committed))))
  t)

;; --- N1+isolation with committed sibling ---
(defun test-mixed-recovery ()
  (reset-dir)
  (let* ((p (wal-path "mixed.wal"))
         (fd (open-wal-file p))
         (applied-nodes '()))
    (write-prepare-record fd 1 10 1234 '(:node "A"))
    (write-prepare-record fd 2 20 4321 '(:node "B"))
    (write-commit-record fd 2 21)
    (close-wal-file fd)
    (recover-from-wal p (lambda (sexp) (push (second sexp) applied-nodes)))
    ;; only the committed tx applies; the prepared tx stays isolated
    (assert (equal applied-nodes '("B")))
    (let ((scan (scan-wal-file p)))
      (assert (eq (gethash 1 (wal-scan-result-tx-table scan)) :prepared))
      (assert (eq (gethash 2 (wal-scan-result-tx-table scan)) :committed))))
  t)

(defun wal-recovery-self-test ()
  (test-in-doubt-retention)
  (test-tail-quarantine)
  (test-rollforward-idempotent)
  (test-mixed-recovery)
  t)
