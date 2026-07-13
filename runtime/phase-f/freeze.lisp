(defpackage :phase-f.freeze
  (:use :cl
        :phase-f.frozen-config
        :phase-f.inlet)
  (:export
   ;; Top-level API (SIGMA-4 F0 / C2)
   #:frozen-semantics
   #:semantic-inlet
   ;; Re-exports for downstream
   #:frozen-config-p
   #:frozen-config-inlet-key
   #:frozen-config-version
   #:frozen-config-meta
   #:semantic-inlet-p
   #:semantic-inlet-value
   #:semantic-inlet-inlet-key
   #:semantic-inlet-version
   #:bind-inlet
   #:normalize-output))

(in-package :phase-f.freeze)

;; ============================================================
;; Phase F — Semantic Freeze Layer
;; ============================================================
;;
;; F = frozen_semantics(config)
;; S = semantic_inlet(F)
;;
;; Phase F is stateless and holds no semantic information itself.
;; It freezes exactly one semantic inlet as the official entry
;; point for LLM output normalization.
;;
;; SIGMA-4:
;;   F0:  inlet = A
;;   C2:  bind(LLM_output → inlet)
;; ============================================================

(defun frozen-semantics (config)
  "F = frozen_semantics(config)
Create a frozen semantic configuration from a config plist.
CONFIG is a plist with keys :inlet-key and :version.
Defaults: inlet-key = :a (Phase A History), version = 0.

Returns a FROZEN-CONFIG instance."
  (let ((inlet-key (or (getf config :inlet-key) :a))
        (version   (or (getf config :version)   0)))
    (make-frozen-config :inlet-key inlet-key
                        :version   version
                        :meta      config)))

(defun semantic-inlet (frozen-config inlet-value)
  "S = semantic_inlet(F)
Bind a concrete inlet value to the frozen configuration.
Returns the unique SEMANTIC-INLET for this F instance.

FROZEN-CONFIG: the frozen-config returned by frozen-semantics.
INLET-VALUE:   the concrete inlet (e.g. a Phase A History).

The returned inlet is the exclusive entry point (FINV-1)."
  (bind-inlet frozen-config inlet-value))