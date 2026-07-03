(in-package :experiment)

(defun build-basin-map (graph nodes steps)
  (let ((table (make-hash-table)))
    (dolist (n nodes)
      (let ((a (find-attractor graph n steps)))
        (push n (gethash a table))))
    table))

(defstruct basin
  attractor
  nodes
  mass
  ratio)

(defun build-basin-structure (basin-map total-nodes)
  (let ((result '()))
    (maphash
     (lambda (attr nodes)
       (let* ((mass (length nodes))
              (ratio (/ mass total-nodes)))
         (push (make-basin
                :attractor attr
                :nodes nodes
                :mass mass
                :ratio ratio)
               result)))
     basin-map)
    result))