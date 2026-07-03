(defpackage :phase-c.event-abi
  (:use :cl :phase-a.event)
  (:export
   #:*event-abi-version*
   #:role-of
   #:role-from-event-type
   #:normalize-event))

(in-package :phase-c.event-abi)

;; ABI version (context only)
(defparameter *event-abi-version* :event-v0)

(defun role-from-event-type (type)
  "Current minimal ABI mapping."
  (cond
    ((eq type :user)      :user)
    ((eq type :assistant) :assistant)
    ((eq type :system)    :system)
    (t                    :unknown)))

(defun role-of (event)
  "ABI-level interpretation over full event.
将来 payload/context を見る余地を残す。"
  (role-from-event-type (event-type event)))

(defun normalize-event (event)
  "Pure structural normalization (NO ABI).
Event → (type payload)"
  (list (event-type event)
        (event-payload event)))
