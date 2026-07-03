(defpackage :ir
  (:use :cl)
  (:export :make-ir :ir
           :ir-ctx-id :ir-pos :ir-phase :ir-token :ir-score))

(in-package :ir)

(defstruct ir
  ctx-id
  pos
  phase
  token
  score)
