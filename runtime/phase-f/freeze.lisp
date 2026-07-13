(defpackage :phase-f.freeze
  (:use :cl
        :phase-f.frozen-config
        :phase-f.inlet)
  (:export
   ;; SIGMA-4 API
   #:frozen-semantics
   #:semantic-inlet

   ;; Frozen configuration
   #:frozen-config-p
   #:frozen-config-inlet-key
   #:frozen-config-version
   #:frozen-config-meta

   ;; Semantic inlet
   #:semantic-inlet-p
   #:semantic-inlet-value
   #:semantic-inlet-inlet-key
   #:semantic-inlet-version

   ;; Utilities
   #:bind-inlet
   #:normalize-output))

(in-package :phase-f.freeze)

;; ============================================================
;; Phase F — Semantic Freeze Layer
;;
;; F = frozen_semantics(config)
;; S = semantic_inlet(F)
;;
;; This layer freezes exactly one semantic inlet for runtime
;; integration. It contains no mutable runtime state and performs
;; no semantic interpretation itself.
;;
;; SIGMA-4
;;
;;   F0:
;;       F = frozen_semantics(config)
;;
;;   C2:
;;       S = semantic_inlet(F)
;;
;; ============================================================

(defun frozen-semantics (&optional (config '()))
  "Create an immutable frozen semantic configuration.

CONFIG is a property list.

Recognized keys:

  :INLET-KEY   keyword   (default :A)
  :VERSION     integer   (default 0)

Returns a FROZEN-CONFIG."

  (assert (listp config)
          (config)
          "CONFIG must be a list.")

  (assert (evenp (length config))
          (config)
          "CONFIG must be a property list.")

  (assert
   (loop for (key value) on config by #'cddr
         always (keywordp key))
   (config)
   "CONFIG keys must be keywords.")

  (make-frozen-config
   :inlet-key (or (getf config :inlet-key) :a)
   :version   (or (getf config :version) 0)
   :meta      config))

(defun semantic-inlet (frozen-config inlet-value)
  "Bind a concrete runtime inlet to a frozen configuration.

Returns an immutable SEMANTIC-INLET.

This function performs no normalization and no semantic
interpretation."

  (assert (frozen-config-p frozen-config)
          (frozen-config)
          "FROZEN-CONFIG must be a FROZEN-CONFIG instance.")

  (bind-inlet frozen-config inlet-value))
