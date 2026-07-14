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
;; Frozen Config — immutable semantic freeze configuration
;; ------------------------------------------------------------
;; FINV-4: Frozen inlet is explicit and versioned
;; FINV-6: Removal or change of inlet requires new F version

(defstruct (frozen-config
             (:constructor %make-frozen-config (inlet-key version meta))
             (:copier nil))
  (inlet-key :a   :type keyword :read-only t)
  (version   0    :type integer :read-only t)
  (meta      nil  :type list    :read-only t))

(defun make-frozen-config (&key (inlet-key :a) (version 0) meta)
  "Create a new frozen semantic configuration.
inlet-key designates which phase provides the inlet (:a = History).
version must be incremented on any inlet change (FINV-6)."
  (check-type inlet-key keyword)
  (check-type version integer)
  (%make-frozen-config inlet-key version
                       (list :source  :phase-f
                             :version version
                             :inlet   inlet-key
                             :extra   meta)))
