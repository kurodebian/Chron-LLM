(defpackage :ir
  (:use :cl)
  (:export
   #:make-ir
   #:ir-p
   #:ir-ctx-id
   #:ir-pos
   #:ir-phase
   #:ir-token
   #:ir-score))

(in-package :ir)

;; ------------------------------------------------------------
;; Intermediate Representation (IR)
;;
;; Immutable observation record emitted by the runtime callback.
;;
;; Guarantees:
;;   - represents one decoding observation
;;   - contains no semantic interpretation
;;   - preserves callback emission order via POS
;;   - suitable for deterministic replay and analysis
;;
;; IR is observational data only and never participates in
;; authoritative runtime state.
;; ------------------------------------------------------------

(defstruct ir
  ;; Runtime context identifier.
  ctx-id

  ;; Sequential decoding position.
  pos

  ;; Runtime phase identifier.
  ;;
  ;; Typical values:
  ;;   0 : prefill
  ;;   1 : generation
  ;;   2 : finalize
  phase

  ;; Generated token identifier.
  token

  ;; Token score (implementation-defined).
  score)