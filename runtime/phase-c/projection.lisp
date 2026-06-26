(defpackage :phase-c.projection
  (:use :cl
        :phase-a.history
        :phase-a.event
        :phase-c.model
        :phase-c.justification
        :phase-c.event-abi)
  (:export
   #:project-model
   #:justify-model))

(in-package :phase-c.projection)

(defun project-model (h)
  "H → M : semantic projection via ABI.
normalize-event は純粋構造、role-of(event) が唯一の意味射影。"

  (let* ((events  (history-snapshot h))
         (triples
           (mapcar (lambda (e)
                     (list (role-of e)
                           (event-type e)
                           (event-payload e)))
                   events)))

    (make-model
     :data  triples
     :meta  (list :source  :phase-c
                  :version 1
                  :abi     *event-abi-version*)
     :shape :sequence)))

(defun justify-model (m)
  "Minimal provenance-bearing justification."
  (make-justification
   (list :derived-from (model-data m)
         :meta         (model-meta m)
         :timestamp    :t0)))
