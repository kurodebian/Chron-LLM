// macros/dsl.spec
// =============================================================================
// Chron-LLM Invariant Verification DSL Specification
// Macro Engine for Phase Pre/Post-Condition Assertions & Invariant Auditing
// =============================================================================

# SECTION 1: DSL DESIGN GOALS & INVARIANT REGISTRY

1.1 Verification Design Goals
  - IR 仕様書に定義されたすべての System Invariants (例: INV_CFFI_*, INV_TYPES_*) を
    コード内の直接的な宣言として埋め込み、実行時 (Runtime) に事前・事後条件として自動検証する。
  - 最適化設定 (*ENABLE-INVARIANT-CHECKING*) により、本番環境 (Production Build) では
    ゼロコストで検証コードを消去可能にする。
  - 不変条件違反の発生時に、違反した Invariant ID、コンテキストデータ、入力・出力引数を
    厳密に特定可能なシグナリング機構を提供する。

1.2 Global Invariant Registry
(defvar *invariant-registry* (make-hash-table :test 'eq)
  "Global lookup table mapping invariant IDs (symbols) to their semantic descriptions and handler functions.")

(defmacro define-invariant (id description &body predicate-body)
  "Registers a system invariant with a descriptive documentation string and validation logic.
   
   Example:
     (define-invariant :inv-types-1-immutability
       \"Cross-phase structures must be immutable.\"
       (lambda (obj) (slot-read-only-p obj)))"
  `(eval-when (:compile-toplevel :load-toplevel :execute)
     (setf (gethash ',id *invariant-registry*)
           (list :description ,description
                 :predicate (lambda (,@(car predicate-body))
                              ,@(cdr predicate-body))))))

// =============================================================================

# SECTION 2: CORE DSL MACROS

2.1 Execution & Runtime Control Dynamics
(defvar *enable-invariant-checking* t
  "Global dynamic switch for invariant checking. When set to NIL at compile-time, 
   DSL macros expand into zero-overhead code without assertion overhead.")

(define-condition invariant-violation (error)
  ((id          :initarg :id          :reader violation-id)
   (phase       :initarg :phase       :reader violation-phase)
   (context-kind:initarg :context-kind:reader violation-context-kind) ;; :PRE or :POST
   (form        :initarg :form        :reader violation-form)
   (value-alist :initarg :value-alist :reader violation-value-alist))
  (:report (lambda (condition stream)
             (format stream "[INVARIANT VIOLATION] Phase: ~A (~A-condition) | Invariant: ~A~%Form: ~S~%Captured Values: ~S~%"
                     (violation-phase condition)
                     (violation-context-kind condition)
                     (violation-id condition)
                     (violation-form condition)
                     (violation-value-alist condition)))))

2.2 Atomic Verification Macro: check-invariant
(defmacro check-invariant (id phase-id context-kind form &rest bindings)
  "Evaluates FORM against a specified INVARIANT ID.
   
   Bindings are passed as an alist for diagnostic context capturing."
  (if *enable-invariant-checking*
      (let ((result-var (gensym "RESULT"))
            (eval-bindings (mapcar (lambda (b) `(cons ',b ,b)) bindings)))
        `(let ((,result-var ,form))
           (unless ,result-var
             (error 'invariant-violation
                    :id ',id
                    :phase ',phase-id
                    :context-kind ',context-kind
                    :form ',form
                    :value-alist (list ,@eval-bindings)))
           ,result-var))
      `(progn ,form)))

2.3 Phase Function Definition Macro: defphase
(defmacro defphase (name-and-options (&rest args) &body body)
  "Defines a Chron-LLM Phase transformation function wrapped with explicit invariant contracts.
   
   Syntax:
     (defphase (name :phase phase-id) (args...)
       (:pre (invariant-id form)*)
       (:post (invariant-id form)*)
       body...)"
  (let* ((name (if (listp name-and-options) (first name-and-options) name-and-options))
         (phase-id (if (listp name-and-options) (getf (cdr name-and-options) :phase) :unknown))
         (pre-clauses nil)
         (post-clauses nil)
         (actual-body nil))
    
    ;; Parse Declarative Clauses
    (dolp (form body)
      (cond
        ((and (consp form) (eq (car form) :pre))
         (setf pre-clauses (cdr form)))
        ((and (consp form) (eq (car form) :post))
         (setf post-clauses (cdr form)))
        (t (push form actual-body))))
    
    (setf actual-body (nreverse actual-body))
    
    (let ((result-var (gensym "RESULT"))
          (arg-syms (mapcar (lambda (arg) (if (listp arg) (car arg) arg)) args)))
      `(defun ,name (,@args)
         (declare (ignorable ,@arg-syms))
         
         ;; --- 1. Pre-condition Invariant Assertions ---
         ,@(mapcar (lambda (clause)
                     (destructuring-bind (inv-id check-form) clause
                       `(check-invariant ,inv-id ,phase-id :pre ,check-form ,@arg-syms)))
                   pre-clauses)
         
         ;; --- 2. Body Execution & Post-condition Invariant Assertions ---
         (let ((,result-var (progn ,@actual-body)))
           ,@(mapcar (lambda (clause)
                       (destructuring-bind (inv-id check-form) clause
                         ;; The special symbol %RESULT% is made available in post-checks
                         `(let ((%result% ,result-var))
                            (declare (ignorable %result%))
                            (check-invariant ,inv-id ,phase-id :post ,check-form %result% ,@arg-syms))))
                     post-clauses)
           ,result-var)))))

// =============================================================================

# SECTION 3: EXPANSION DYNAMICS & MACROEXPAND DEMONSTRATION

3.1 Source Macro Call
(defphase (project-history-to-view :phase :phase-b) (history-state filter-mask)
  (:pre
   (:inv-types-1-immutability (typep history-state 'history-state)))
  (:post
   (:inv-types-1-immutability (typep %result% 'projection-view))
   (:inv-types-3-foreign-isolation (null (proj-source-history-id %result%))))
  
  ;; Business Logic Form
  (make-projection-view
   :id "proj-gen-001"
   :source-history-id (history-id history-state)
   :filter-mask filter-mask
   :transformed-prompt "Processed prompt"
   :token-estimates 0))

3.2 Expanded Standard Common Lisp Form (Optimized Readability)
(defun project-history-to-view (history-state filter-mask)
  (declare (ignorable history-state filter-mask))
  
  ;; --- PRE-CONDITIONS ---
  (let ((#:result1 (typep history-state 'history-state)))
    (unless #:result1
      (error 'invariant-violation
             :id ':inv-types-1-immutability
             :phase ':phase-b
             :context-kind ':pre
             :form '(typep history-state 'history-state)
             :value-alist (list (cons 'history-state history-state)
                                (cons 'filter-mask filter-mask)))))
  
  ;; --- BODY & POST-CONDITIONS ---
  (let ((#:result2
          (progn
            (make-projection-view
             :id "proj-gen-001"
             :source-history-id (history-id history-state)
             :filter-mask filter-mask
             :transformed-prompt "Processed prompt"
             :token-estimates 0))))
    
    (let ((%result% #:result2))
      (declare (ignorable %result%))
      
      (let ((#:result3 (typep %result% 'projection-view)))
        (unless #:result3
          (error 'invariant-violation
                 :id ':inv-types-1-immutability
                 :phase ':phase-b
                 :context-kind ':post
                 :form '(typep %result% 'projection-view)
                 :value-alist (list (cons '%result% %result%)
                                    (cons 'history-state history-state)
                                    (cons 'filter-mask filter-mask)))))
      
      (let ((#:result4 (null (proj-source-history-id %result%))))
        (unless #:result4
          (error 'invariant-violation
                 :id ':inv-types-3-foreign-isolation
                 :phase ':phase-b
                 :context-kind ':post
                 :form '(null (proj-source-history-id %result%))
                 :value-alist (list (cons '%result% %result%)
                                    (cons 'history-state history-state)
                                    (cons 'filter-mask filter-mask))))))
    #:result2))

// =============================================================================

# SECTION 4: SYSTEM INVARIANT DEFPHASE INTEGRATION EXAMPLES

4.1 Verifying Foreign Isolation (INV_CFFI_3 / INV_TYPES_3)
(defphase (extract-normalized-tokens :phase :phase-f) (foreign-buf token-count)
  (:pre
   (:inv-cffi-1-no-leak (not (cffi:null-pointer-p foreign-buf)))
   (:inv-cffi-2-thread-safety (> token-count 0)))
  (:post
   ;; Ensure the return value is a pure Common Lisp Vector with no C Pointers attached
   (:inv-types-3-foreign-isolation 
    (and (typep %result% 'normalized-rep)
         (not (typep (norm-rep-parsed-sexp %result%) 'cffi:foreign-pointer)))))
  
  (let ((tokens-array (make-array token-count :element-type '(signed-byte 32))))
    ;; C Foreign Memory Copy Operation
    (dotimes (i token-count)
      (setf (aref tokens-array i)
            (cffi:mem-aref foreign-buf :int32 i)))
    
    (make-normalized-rep
     :id "norm-stream-001"
     :parsed-sexp tokens-array
     :valid-p t)))
