(defpackage :phase-f.frozen-config
  (:use :cl)
  (:export
   #:make-frozen-config
   #:frozen-config-p
   #:frozen-config-inlet-key
   #:frozen-config-version
   #:frozen-config-meta))

(in-package :phase-f.frozen-config)

;; ------------------------------------------------------------
;; Phase F Frozen Configuration
;;
;; Immutable configuration that freezes the semantic inlet.
;;
;; Guarantees:
;;   - explicit inlet selection
;;   - explicit versioning
;;   - immutable after construction
;;
;; FINV-7
;;   Frozen inlet is explicit and versioned.
;;
;; FINV-9
;;   Replacing the inlet requires a new Phase F version.
;; ------------------------------------------------------------

(defstruct (frozen-config
             (:constructor %make-frozen-config
                 (inlet-key version meta))
             (:copier nil))
  (inlet-key :a
             :type keyword
             :read-only t)
  (version 0
           :type (integer 0 *)
           :read-only t)
  (meta nil
        :type t
        :read-only t))

(defun make-frozen-config
    (&key
       (inlet-key :a)
       (version 0)
       meta)
  "Create an immutable frozen semantic configuration."

  (check-type inlet-key keyword)
  (check-type version (integer 0 *))

  ;; META is implementation-defined and intentionally unconstrained.

  (%make-frozen-config
   inlet-key
   version
   meta))
