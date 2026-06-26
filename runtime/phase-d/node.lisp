(defpackage :phase-d.node
  (:use :cl :phase-a.event)
  (:export
   #:make-node
   #:node-p
   #:node-id
   #:node-event
   #:node-meta
   #:node-id-from-index))

(in-package :phase-d.node)

(defstruct node
  id      ;; node-id（ここでは event-index をそのまま使う）
  event   ;; 元の Phase A event
  meta)   ;; 将来: role/type/phase などを持てる

(defun node-id-from-index (i)
  "最小実装: index をそのまま node-id として扱う。
将来、永続IDやハッシュに差し替え可能な拡張点。"
  i)
