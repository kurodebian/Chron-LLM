(in-package :chron-r2-0-a)

(defstruct (prefill-state (:constructor make-prefill-state (context target-id hash)))
  (context nil :type list :read-only t) (target-id nil :read-only t) (hash "" :type string :read-only t))

(defun canonical-prompt (context)
  (with-output-to-string (stream)
    (dolist (node context)
      (format stream "(prompt~% (:node ~S~%  :type ~S~%  :content ~S~%  :feedback ~S))~%"
              (context-node-id node) (context-node-type node)
              (context-node-content node) (context-node-feedbacks node)))))

(defun build-prefill-state (graph store target-id &key (include-evaluations nil)
                                                 (prompt-builder #'canonical-prompt))
  (let* ((context (project-context graph store target-id :include-evaluations include-evaluations))
         (prompt (funcall prompt-builder context)))
    (unless (stringp prompt) (error "Prompt builder must return a string."))
    (make-prefill-state context target-id (sha256-string prompt))))
