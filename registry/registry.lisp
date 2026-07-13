(in-package :chron-r2-0-a)

(defstruct (world-registry (:constructor make-world-registry (&key graph memory)))
  ;; Entries are insertion ordered: (world-id . world); ancestry is (child . parent).
  (worlds nil :type list) (ancestry nil :type list) (active-id nil) graph memory)

(defun find-world (registry world-id)
  (cdr (assoc world-id (world-registry-worlds registry) :test #'equal)))

(defun list-worlds (registry)
  (mapcar #'cdr (world-registry-worlds registry)))

(defun active-world (registry)
  (and (world-registry-active-id registry)
       (find-world registry (world-registry-active-id registry))))

(defun %registry-shared-objects-p (registry world)
  (and (or (null (world-registry-graph registry))
           (eq (world-registry-graph registry) (world-graph-ref world)))
       (or (null (world-registry-memory registry))
           (eq (world-registry-memory registry) (world-memory-ref world)))))

(defun register-world (registry world &key parent-id)
  "Register identity and ancestry.  This indexes views but never changes truth."
  (unless (world-p world) (error "Only a world may be registered."))
  (when (find-world registry (world-id world)) (error "World id has already been used: ~S" (world-id world)))
  (unless (%registry-shared-objects-p registry world)
    (error "Every registered world must share the canonical graph and memory."))
  (when (and parent-id (not (find-world registry parent-id)))
    (error "Parent world must already be registered: ~S" parent-id))
  (unless (world-registry-graph registry)
    (setf (world-registry-graph registry) (world-graph-ref world)
          (world-registry-memory registry) (world-memory-ref world)))
  (setf (world-registry-worlds registry)
        (append (world-registry-worlds registry) (list (cons (world-id world) world))))
  (when parent-id
    (setf (world-registry-ancestry registry)
          (append (world-registry-ancestry registry) (list (cons (world-id world) parent-id)))))
  world)

(defun set-active-world (registry world-id)
  (let ((next (find-world registry world-id)) (current (active-world registry)))
    (unless next (error "Unknown world id: ~S" world-id))
    (when (eq (world-lifecycle next) :archived) (error "Archived worlds cannot become active."))
    (when (and current (not (eq current next))) (%set-world-lifecycle! current :inactive))
    (%set-world-lifecycle! next :active)
    (setf (world-registry-active-id registry) world-id)
    next))

(defun archive-world (registry world-id)
  (let ((world (find-world registry world-id)))
    (unless world (error "Unknown world id: ~S" world-id))
    (%set-world-lifecycle! world :archived)
    (when (equal world-id (world-registry-active-id registry))
      (setf (world-registry-active-id registry) nil))
    world))
