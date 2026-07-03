(defpackage :phase-d.edge
  (:use :cl)
  (:export
   #:make-edge
   #:edge-p
   #:edge-from
   #:edge-to
   #:edge-relation
   #:edge-strength
   #:edge-guard
   #:edge-meta))

(in-package :phase-d.edge)

(defstruct edge
  from       ;; node-id
  to         ;; node-id
  relation   ;; :temporal / :reply / :causal / ...
  strength   ;; 0.0〜1.0（因果の強さ）
  guard      ;; optional predicate（まだ未使用だが拡張点）
  meta)      ;; e.g. :from-index, :to-index, :source :phase-d
