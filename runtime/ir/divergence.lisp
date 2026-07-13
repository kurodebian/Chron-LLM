(defpackage :ir-divergence
  (:use :cl
        :ir
        :ir-stream)
  (:export
   #:extract-actions
   #:run-ir-trial
   #:divergence-profile))

(in-package :ir-divergence)

;; ------------------------------------------------------------
;; IR Divergence Analysis
;;
;; Utilities for measuring divergence between multiple decoding
;; runs using the Phase-1 IR callback stream.
;;
;; This layer is observational only.
;; It never affects decoding or runtime behavior.
;; ------------------------------------------------------------

(defun extract-actions (ir-stream)
  "Extract Phase-1 action IRs ordered by decoding position."

  (let ((sorted (sort (copy-seq ir-stream)
                      #'<
                      :key #'ir-pos)))
    (loop
      for ir across sorted
      when (= (ir-phase ir) 1)
        collect ir)))

(defun run-ir-trial (prompt)
  "Execute one decoding run and return Phase-1 IRs."

  (clear-ir-stream)

  (llama-run *model* *ctx* prompt)

  (coerce (extract-actions *ir-stream*)
          'vector))

(defun divergence-profile (prompt n-runs)
  "Compute token agreement statistics across repeated runs."

  (let* ((runs
           (loop repeat n-runs
                 collect (run-ir-trial prompt)))

         (max-len
           (apply #'min
                  (mapcar #'length runs))))

    (loop
      for step from 0 below max-len

      for tokens =
        (mapcar (lambda (seq)
                  (ir-token (aref seq step)))
                runs)

      for all-same =
        (apply #'= tokens)

      collect
        (list
         :step step
         :all-same all-same
         :p-same
         (/ (float (count (first tokens) tokens))
            (length tokens))))))