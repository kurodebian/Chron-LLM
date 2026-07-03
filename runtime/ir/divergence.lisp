(defpackage :ir-divergence
  (:use :cl :ir :ir-stream)
  (:export :extract-actions :run-ir-trial :divergence-profile))

(in-package :ir-divergence)

(defun extract-actions (ir-stream)
  (let ((sorted (sort (copy-seq ir-stream) #'< :key #'ir-pos)))
    (loop for ir across sorted
          when (= (ir-phase ir) 1)
            collect ir)))

(defun run-ir-trial (prompt)
  (clear-ir-stream)
  (llama-run *model* *ctx* prompt)
  (coerce (extract-actions *ir-stream*) 'vector))

(defun divergence-profile (prompt n-runs)
  (let* ((runs (loop repeat n-runs collect (run-ir-trial prompt)))
         (max-len (apply #'min (mapcar #'length runs))))
    (loop for step from 0 below max-len
          for tokens-at-t =
            (mapcar (lambda (seq) (ir-token (aref seq t))) runs)
          for all-same = (apply #'= tokens-at-t)
          collect (list :t t
                        :all-same all-same
                        :p-same (/ (count (car tokens-at-t) tokens-at-t)
                                   (length tokens-at-t))))))
