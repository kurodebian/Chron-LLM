(defpackage :chronos-r0.chat
  (:use :cl
        :chronos-r0.history
        :chronos-r0.prompt
        :chronos-r0.llama
        :chronos-r0.trace)
  (:export
   :session
   :session-model
   :session-history
   :make-new-session
   :chat
   :start-chat))

(in-package :chronos-r0.chat)

;; ----------------------------
;; STATE
;; ----------------------------
(defstruct session
  model
  history)

(defun make-new-session (&key model)
  (make-session
   :model model
   :history (chronos-r0.history:make-history)))

;; ----------------------------
;; INTERNAL
;; ----------------------------
(defun extract-generation (raw)
  raw)

(defun make-assistant-event (text)
  (chronos-r0.history:make-history-event
   :role :assistant
   :content text))

;; ----------------------------
;; CORE STEP
;; ----------------------------
(defun chat (session user-text)
  (let* ((history        (session-history session))
         (history-before (chronos-r0.history:history-copy history)))

    ;; user event
    (chronos-r0.history:history-append
     history
     (chronos-r0.history:make-history-event
      :role :user
      :content user-text))

    (let* ((prompt              (chronos-r0.prompt:project-to-prompt history))
           (prompt-length       (length prompt))
           (history-size-before (chronos-r0.history:history-size history))

           (raw    (chronos-r0.llama:llama-run prompt))
           (parsed (extract-generation raw)))

      ;; assistant event
      (chronos-r0.history:history-append
       history
       (make-assistant-event parsed))

      ;; trace
      (chronos-r0.trace:log-trace
       (chronos-r0.trace:make-r0-trace
        :user-text user-text
        :prompt prompt
        :raw raw
        :parsed parsed
        :history-before history-before
        :history-after (chronos-r0.history:history-copy history)
        :prompt-length prompt-length
        :response-length (length parsed)
        :history-size-before history-size-before
        :history-size-after (chronos-r0.history:history-size history))))

    session))

;; ----------------------------
;; SAFE UI LOOP
;; ----------------------------
(defun start-chat ()
  (let ((s (make-new-session)))
    (loop
      (format t "~&You> ")
      (finish-output) ;; ★重要：flush

      (let ((in (read-line *standard-input* nil :exit)))
        (when (or (null in) (eq in :exit))
          (return))

        (chat s in)

        (let* ((hist (session-history s))
               (events (chronos-r0.history:history-events hist))
               (last (loop for i downfrom (1- (length events)) to 0
                           for e = (aref events i)
                           when (eq (chronos-r0.history:history-event-role e) :assistant)
                           do (return e))))

          (format t "~&AI> ~A~%"
                  (if last
                      (chronos-r0.history:history-event-content last)
                      "")))))))