(defpackage :chron-r2-0-c
  (:use :cl :chron-r2-0-a)
  (:export
   #:+observation-schema-version+
   #:world-observation #:world-observation-p #:world-observation-schema-version
   #:world-observation-world-id #:world-observation-root-node-id
   #:world-observation-head-node-id #:world-observation-projection-policy
   #:world-observation-metadata #:world-observation-lifecycle
   #:world-observation-parent-world-id
   #:registry-observation #:registry-observation-p #:registry-observation-schema-version
   #:registry-observation-world-ids #:registry-observation-active-world-id
   #:registry-observation-archived-world-ids
   #:ancestry-observation #:ancestry-observation-p #:ancestry-observation-schema-version
   #:ancestry-observation-world-id #:ancestry-observation-parent-world-id
   #:ancestry-observation-ancestry-path
   #:diff-observation #:diff-observation-p #:diff-observation-schema-version
   #:diff-observation-changed-p #:diff-observation-changed-fields
   #:build-world-observation #:build-registry-observation #:build-ancestry-observation
   #:build-diff-observation #:describe-world #:describe-registry #:describe-ancestry
   #:describe-diff))

(in-package :chron-r2-0-c)

;;; C1 is intentionally a data-only boundary. Builders take primitive snapshot
;;; values, not World/Registry objects, and therefore cannot inspect or mutate
;;; domain internals.
(defconstant +observation-schema-version+ 1)

(defun %primitive-leaf-p (value)
  (or (null value)
      (eq value t)
      (stringp value)
      (numberp value)
      (characterp value)
      (keywordp value)))

(defun %primitive-tree-p (value)
  (cond ((%primitive-leaf-p value) t)
        ((consp value) (and (%primitive-tree-p (car value))
                            (%primitive-tree-p (cdr value))))
        (t nil)))

(defun %copy-primitive-tree (value)
  (cond ((stringp value) (copy-seq value))
        ((consp value) (cons (%copy-primitive-tree (car value))
                             (%copy-primitive-tree (cdr value))))
        (t value)))

(defun %require-primitive-tree (value field)
  (unless (%primitive-tree-p value)
    (error "Observation field ~S must contain only primitive snapshot values." field))
  (%copy-primitive-tree value))

(defstruct (world-observation
             (:constructor %make-world-observation
                 (schema-version world-id root-node-id head-node-id projection-policy
                  metadata lifecycle parent-world-id))
             (:conc-name %world-observation-)
             (:type vector))
  (schema-version +observation-schema-version+ :read-only t)
  (world-id nil :read-only t)
  (root-node-id nil :read-only t)
  (head-node-id nil :read-only t)
  (projection-policy nil :read-only t)
  (metadata nil :read-only t)
  (lifecycle nil :read-only t)
  (parent-world-id nil :read-only t))

(defstruct (registry-observation
             (:constructor %make-registry-observation
                 (schema-version world-ids active-world-id archived-world-ids))
             (:conc-name %registry-observation-)
             (:type vector))
  (schema-version +observation-schema-version+ :read-only t)
  (world-ids nil :read-only t)
  (active-world-id nil :read-only t)
  (archived-world-ids nil :read-only t))

(defstruct (ancestry-observation
             (:constructor %make-ancestry-observation
                 (schema-version world-id parent-world-id ancestry-path))
             (:conc-name %ancestry-observation-)
             (:type vector))
  (schema-version +observation-schema-version+ :read-only t)
  (world-id nil :read-only t)
  (parent-world-id nil :read-only t)
  (ancestry-path nil :read-only t))

(defstruct (diff-observation
             (:constructor %make-diff-observation
                 (schema-version changed-p changed-fields))
             (:conc-name %diff-observation-)
             (:type vector))
  (schema-version +observation-schema-version+ :read-only t)
  (changed-p nil :read-only t)
  (changed-fields nil :read-only t))

(defun world-observation-p (value)
  (and (vectorp value) (= (length value) 8) (eq (aref value 0) +observation-schema-version+)))

(defun world-observation-equal (left right)
  (and (world-observation-p left) (world-observation-p right)
       (equal (world-observation-world-id left) (world-observation-world-id right))
       (equal (world-observation-root-node-id left) (world-observation-root-node-id right))
       (equal (world-observation-head-node-id left) (world-observation-head-node-id right))
       (equal (world-observation-projection-policy left) (world-observation-projection-policy right))
       (equal (world-observation-metadata left) (world-observation-metadata right))
       (equal (world-observation-lifecycle left) (world-observation-lifecycle right))
       (equal (world-observation-parent-world-id left) (world-observation-parent-world-id right))))

(defun world-observation-schema-version (value) (%world-observation-schema-version value))
(defun world-observation-world-id (value) (%copy-primitive-tree (%world-observation-world-id value)))
(defun world-observation-root-node-id (value) (%copy-primitive-tree (%world-observation-root-node-id value)))
(defun world-observation-head-node-id (value) (%copy-primitive-tree (%world-observation-head-node-id value)))
(defun world-observation-projection-policy (value) (%copy-primitive-tree (%world-observation-projection-policy value)))
(defun world-observation-metadata (value) (%copy-primitive-tree (%world-observation-metadata value)))
(defun world-observation-lifecycle (value) (%world-observation-lifecycle value))
(defun world-observation-parent-world-id (value) (%copy-primitive-tree (%world-observation-parent-world-id value)))

(defun registry-observation-p (value)
  (and (vectorp value) (= (length value) 4) (eq (aref value 0) +observation-schema-version+)))

(defun registry-observation-equal (left right)
  (and (registry-observation-p left) (registry-observation-p right)
       (equal (registry-observation-world-ids left) (registry-observation-world-ids right))
       (equal (registry-observation-active-world-id left) (registry-observation-active-world-id right))
       (equal (registry-observation-archived-world-ids left) (registry-observation-archived-world-ids right))))

(defun registry-observation-schema-version (value) (%registry-observation-schema-version value))
(defun registry-observation-world-ids (value) (%copy-primitive-tree (%registry-observation-world-ids value)))
(defun registry-observation-active-world-id (value) (%copy-primitive-tree (%registry-observation-active-world-id value)))
(defun registry-observation-archived-world-ids (value) (%copy-primitive-tree (%registry-observation-archived-world-ids value)))

(defun ancestry-observation-p (value)
  (and (vectorp value) (= (length value) 4) (eq (aref value 0) +observation-schema-version+)))

(defun ancestry-observation-equal (left right)
  (and (ancestry-observation-p left) (ancestry-observation-p right)
       (equal (ancestry-observation-world-id left) (ancestry-observation-world-id right))
       (equal (ancestry-observation-parent-world-id left) (ancestry-observation-parent-world-id right))
       (equal (ancestry-observation-ancestry-path left) (ancestry-observation-ancestry-path right))))

(defun ancestry-observation-schema-version (value) (%ancestry-observation-schema-version value))
(defun ancestry-observation-world-id (value) (%copy-primitive-tree (%ancestry-observation-world-id value)))
(defun ancestry-observation-parent-world-id (value) (%copy-primitive-tree (%ancestry-observation-parent-world-id value)))
(defun ancestry-observation-ancestry-path (value) (%copy-primitive-tree (%ancestry-observation-ancestry-path value)))

(defun diff-observation-p (value)
  (and (vectorp value) (= (length value) 3) (eq (aref value 0) +observation-schema-version+)))

(defun diff-observation-equal (left right)
  (and (diff-observation-p left) (diff-observation-p right)
       (equal (diff-observation-changed-p left) (diff-observation-changed-p right))
       (equal (diff-observation-changed-fields left) (diff-observation-changed-fields right))))

(defun diff-observation-schema-version (value) (%diff-observation-schema-version value))
(defun diff-observation-changed-p (value) (%diff-observation-changed-p value))
(defun diff-observation-changed-fields (value) (%copy-primitive-tree (%diff-observation-changed-fields value)))

(defun make-world-observation (&key world-id root-node-id head-node-id projection-policy
                                 metadata lifecycle parent-world-id)
  (%make-world-observation
   +observation-schema-version+
   (%require-primitive-tree world-id :world-id)
   (%require-primitive-tree root-node-id :root-node-id)
   (%require-primitive-tree head-node-id :head-node-id)
   (%require-primitive-tree projection-policy :projection-policy)
   (%require-primitive-tree metadata :metadata)
   (%require-primitive-tree lifecycle :lifecycle)
   (%require-primitive-tree parent-world-id :parent-world-id)))

(defun make-registry-observation (&key world-ids active-world-id archived-world-ids)
  (%make-registry-observation
   +observation-schema-version+
   (%require-primitive-tree world-ids :world-ids)
   (%require-primitive-tree active-world-id :active-world-id)
   (%require-primitive-tree archived-world-ids :archived-world-ids)))

(defun make-ancestry-observation (&key world-id parent-world-id ancestry-path)
  (%make-ancestry-observation
   +observation-schema-version+
   (%require-primitive-tree world-id :world-id)
   (%require-primitive-tree parent-world-id :parent-world-id)
   (%require-primitive-tree ancestry-path :ancestry-path)))

(defun make-diff-observation (&key changed-p changed-fields)
  (%make-diff-observation
   +observation-schema-version+
   (%require-primitive-tree changed-p :changed-p)
   (%require-primitive-tree changed-fields :changed-fields)))

(defun %world-diff-fields (left right)
  (let ((fields nil))
    (flet ((record (name getter)
             (when (not (equal (funcall getter left) (funcall getter right)))
               (push name fields))))
      (record :world-id #'world-observation-world-id)
      (record :root-node-id #'world-observation-root-node-id)
      (record :head-node-id #'world-observation-head-node-id)
      (record :projection-policy #'world-observation-projection-policy)
      (record :metadata #'world-observation-metadata)
      (record :lifecycle #'world-observation-lifecycle)
      (record :parent-world-id #'world-observation-parent-world-id))
    (nreverse fields)))

(defun %registry-diff-fields (left right)
  (let ((fields nil))
    (flet ((record (name getter)
             (when (not (equal (funcall getter left) (funcall getter right)))
               (push name fields))))
      (record :world-ids #'registry-observation-world-ids)
      (record :active-world-id #'registry-observation-active-world-id)
      (record :archived-world-ids #'registry-observation-archived-world-ids))
    (nreverse fields)))

(defun %ancestry-diff-fields (left right)
  (let ((fields nil))
    (flet ((record (name getter)
             (when (not (equal (funcall getter left) (funcall getter right)))
               (push name fields))))
      (record :world-id #'ancestry-observation-world-id)
      (record :parent-world-id #'ancestry-observation-parent-world-id)
      (record :ancestry-path #'ancestry-observation-ancestry-path))
    (nreverse fields)))

(defun build-world-observation (world &key parent-world-id)
  (unless (world-p world) (error "BUILD-WORLD-OBSERVATION requires a World."))
  (make-world-observation
   :world-id (world-id world)
   :root-node-id (world-root-node world)
   :head-node-id (world-head-node world)
   :projection-policy (world-projection-policy world)
   :metadata (world-metadata world)
   :lifecycle (world-lifecycle world)
   :parent-world-id parent-world-id))

(defun build-registry-observation (registry)
  (unless (world-registry-p registry) (error "BUILD-REGISTRY-OBSERVATION requires a World Registry."))
  (let ((worlds (list-worlds registry))
        (active (active-world registry)))
    (make-registry-observation
     :world-ids (mapcar #'world-id worlds)
     :active-world-id (and active (world-id active))
     :archived-world-ids
     (loop for world in worlds
           when (eq (world-lifecycle world) :archived)
             collect (world-id world)))))

(defun build-ancestry-observation (registry world-id)
  (unless (world-registry-p registry) (error "BUILD-ANCESTRY-OBSERVATION requires a World Registry."))
  (let ((parent-entry (assoc world-id (chron-r2-0-a::world-registry-ancestry registry) :test #'equal)))
    (unless parent-entry
      (error "Unknown ancestry relationship for world id: ~S" world-id))
    (make-ancestry-observation
     :world-id world-id
     :parent-world-id (cdr parent-entry)
     :ancestry-path (cons world-id (cdr parent-entry)))))

(defun build-diff-observation (left right)
  (let ((changed-fields
          (cond ((and (world-observation-p left) (world-observation-p right))
                 (%world-diff-fields left right))
                ((and (registry-observation-p left) (registry-observation-p right))
                 (%registry-diff-fields left right))
                ((and (ancestry-observation-p left) (ancestry-observation-p right))
                 (%ancestry-diff-fields left right))
                ((equal (type-of left) (type-of right)) nil)
                (t (list :type)))))
    (make-diff-observation
     :changed-p (not (null changed-fields))
     :changed-fields changed-fields)))

(defun describe-world (world &key parent-world-id)
  (build-world-observation world :parent-world-id parent-world-id))

(defun describe-registry (registry)
  (build-registry-observation registry))

(defun describe-ancestry (registry world-id)
  (build-ancestry-observation registry world-id))

(defun describe-diff (left right)
  (build-diff-observation left right))