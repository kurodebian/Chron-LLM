(in-package :chron-llm)

;;; ============================================================
;;; Runtime
;;; ============================================================
;;; Responsibility
;;;
;;;   • Console I/O
;;;   • LLM Invocation
;;;
;;; Runtime does NOT know:
;;;
;;;   • WAL
;;;   • Graph
;;;   • World ID
;;;   • History
;;;   • Immune
;;;   • Projection
;;;
;;; All state management belongs to Kernel.
;;; ============================================================

(defun agent-main-loop (ctx model)

  (declare (ignore ctx model))

  (let ((kernel
         (make-chron-kernel)))

    (loop

      (format t "~&User> ")
      (finish-output)

      (let ((input (read-line)))

        (handler-case

            (progn

              ;; ==============================================
              ;; User -> Kernel
              ;; ==============================================

              (kernel-submit-user-input
               kernel
               input)

              ;; ==============================================
              ;; Build Context View
              ;; ==============================================

              (let* ((state
                      (kernel-current-state
                       kernel))

                     (context
                      (kernel-state-context
                       state)))

                (format t
                        "~&[System] World: ~D  Health: ~A~%"
                        (kernel-state-world-id state)
                        (kernel-state-health state))

                ;; ==========================================
                ;; Prompt Builder
                ;; (Phase4)
                ;; ==========================================

                ;; (let ((prompt
                ;;        (build-prompt
                ;;         context
                ;;         :phi4)))

                ;; ==========================================
                ;; LLM
                ;; ==========================================

                ;; (let ((reply
                ;;        (generate
                ;;         ctx
                ;;         model
                ;;         prompt)))

                ;; ==========================================
                ;; Assistant -> Kernel
                ;; ==========================================

                ;;   (kernel-submit-assistant-reply
                ;;     kernel
                ;;     reply)))

                (declare (ignore context))))

          (error (e)

            (format t
                    "~&[Runtime Error] ~A~%"
                    e)))))))