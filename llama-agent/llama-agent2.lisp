;;;; llama-agent2.lisp
;;;; Chron-LLM Δ3 — Unified Bootloader
;;;; Phase 1.1 Frozen Architecture

(format t "~%====================================================~%")
(format t "🚀 Chron-LLM Δ3 Phase 1.1 Bootloader Starting...~%")
(format t "====================================================~%")

;;; ============================================================
;;; 0. Environment
;;; ============================================================

(defparameter *system-dir*
  (uiop:pathname-directory-pathname *load-pathname*))

(defparameter *use-mock-physical-p* t)

(format t "[1/10] Loading Quicklisp...~%")

(let ((quicklisp-init
       (merge-pathnames
        "quicklisp/setup.lisp"
        (user-homedir-pathname))))

  (if (probe-file quicklisp-init)
      (load quicklisp-init)
      (error "Quicklisp not found.")))

(ql:quickload '(:cffi :babel))

(in-package :cl-user)

(defun load-system-file (filename)
  (let ((path (merge-pathnames filename *system-dir*)))
    (if (probe-file path)
        (progn
          (format t "  -> Loading ~A~%" filename)
          (load path))
        (error "Required file not found: ~A" filename))))

;;; ============================================================
;;; 1. Physical Layer
;;; ============================================================

(format t "~%[2/10] Loading Physical Layer (~A)...~%"
        (if *use-mock-physical-p*
            "MOCK"
            "FFI"))

(if *use-mock-physical-p*
    (load-system-file "ffi-bindings-mock.lisp")
    (load-system-file "ffi-bindings.lisp"))

;;; ============================================================
;;; 2. LLM Interface
;;; ============================================================

(format t "~%[3/10] Loading LLM Interface...~%")
(load-system-file "chron-llm.lisp")

;;; ============================================================
;;; 3. Core
;;; ============================================================

(format t "~%[4/10] Loading Core...~%")
(load-system-file "chron-llm-core.lisp")

;;; ============================================================
;;; 4. Graph
;;; ============================================================

(format t "~%[5/10] Loading Graph Layer...~%")
(load-system-file "chron-llm-graph.lisp")

;;; ============================================================
;;; 5. World
;;; ============================================================

(format t "~%[6/10] Loading World Layer...~%")
(load-system-file "chron-llm-world.lisp")

;;; ============================================================
;;; 6. Immune
;;; ============================================================

(format t "~%[7/10] Loading Immune System...~%")
(load-system-file "chron-llm-immune.lisp")

;;; ============================================================
;;; 7. Runtime
;;; ============================================================

(format t "~%[8/10] Loading Runtime...~%")
(load-system-file "chron-llm-runtime.lisp")

;;; ============================================================
;;; 8. Generation
;;; ============================================================

(format t "~%[9/10] Loading Generation Logic...~%")
(load-system-file "generate.lisp")

;;; ============================================================
;;; 9. Test Wrapper
;;; ============================================================

(format t "~%[10/10] Loading Test Environment...~%")
(load-system-file "run-test.lisp")

(format t "~%====================================================~%")
(format t "✅ Chron-LLM Δ3 Phase 1.1 Boot Completed.~%")
(format t "====================================================~%")

(in-package :chron-llm)

;;; ============================================================
;;; Boot Entry
;;; ============================================================

(defun start-delta3
       (&optional
        (model-path "/path/to/model.gguf"))

  "Chron-LLM Δ3 起動"

  (format t "~%[Boot] Starting Δ3...~%")

  (let* ((model
          (my-llama-model-load model-path))

         (ctx
          (my-llama-init model 4096)))

    (format t "[Boot] Model Loaded.~%")

    (agent-main-loop ctx model)))

(defun start-delta3-stub ()

  "スタブ起動"

  (format t "~%[Boot] Starting Δ3 Stub...~%")

  (agent-main-loop nil nil))