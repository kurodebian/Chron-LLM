// core/types.spec
// =============================================================================
// Chron-LLM Data Structure Specification - Common Lisp & S-Expression Mapping
// Structural Definitions for Phases A through F
// =============================================================================

# SECTION 1: SYSTEM INVARIANTS & BASE TYPES

1.1 Data Model Invariants
  INV_TYPES_1_IMMUTABILITY: States across Phases A, B, D, and E MUST be immutable 
                            (all defstruct slots set to :read-only t where applicable).
  INV_TYPES_2_SEXPR_ROUNDTRIP: Every data structure MUST have a deterministic, 
                               lossless S-expression representation (to-sexp / from-sexp).
  INV_TYPES_3_FOREIGN_ISOLATION: S-expression serialized representations MUST NOT contain 
                                 raw foreign-pointers or C-allocated memory addresses.

1.2 Primitive & Utility Types
  (deftype timestamp () '(unsigned-byte 64))
  (deftype uuid-string () 'string)
  (deftype phase-id () '(member :phase-a :phase-b :phase-c :phase-d :phase-e :phase-f))

// =============================================================================

# SECTION 2: PHASE A - HISTORY (H) STRUCTURES

2.1 Common Lisp Definition
(defstruct (history-event
            (:constructor make-history-event)
            (:conc-name event-)
            (:type list))
  (id        "" :type uuid-string)
  (timestamp 0  :type timestamp)
  (kind      :user-input :type symbol)
  (content   "" :type string)
  (metadata  nil :type list))  ;; Alist of (:key . value)

(defstruct (history-state
            (:constructor make-history-state)
            (:conc-name history-)
            (:copier nil))
  (id         ""  :type uuid-string :read-only t)
  (sequence   #() :type vector      :read-only t) ;; Vector of history-event
  (head-index 0   :type fixnum      :read-only t))

2.2 Canonical S-Expression Format
;; History Event:
;; (:event :id "evt-1001" :timestamp 1700000000 :kind :user-input :content "Hello" :metadata ((:source . :cli)))

;; History State:
;; (:history
;;   :id "hist-001"
;;   :head-index 1
;;   :events ((:event :id "evt-1001" :timestamp 1700000000 :kind :user-input :content "Hello" :metadata nil)))

// =============================================================================

# SECTION 3: PHASE B - PROJECTION (M) STRUCTURES

3.1 Common Lisp Definition
(defstruct (projection-view
            (:constructor make-projection-view)
            (:conc-name proj-)
            (:copier nil))
  (id                ""  :type uuid-string :read-only t)
  (source-history-id ""  :type uuid-string :read-only t)
  (filter-mask       nil :type list        :read-only t) ;; List of event kinds to include
  (transformed-prompt "" :type string      :read-only t)
  (token-estimates   0   :type fixnum      :read-only t))

3.2 Canonical S-Expression Format
;; Projection View:
;; (:projection-view
;;   :id "proj-5501"
;;   :source-history-id "hist-001"
;;   :filter-mask (:user-input :system-prompt)
;;   :transformed-prompt "[System] ... [User] Hello"
;;   :token-estimates 12)

// =============================================================================

# SECTION 4: PHASE C - SEMANTIC MODEL (S) STRUCTURES

4.1 Common Lisp Definition
;; Note: Phase C handles LLM interaction. Foreign memory pointers are contained here
;; and must NOT leak into S-expressions.
(defstruct (semantic-state
            (:constructor make-semantic-state)
            (:conc-name semantic-)
            (:copier nil))
  (id              ""  :type uuid-string          :read-only t)
  (projection-id   ""  :type uuid-string          :read-only t)
  (tokens          #() :type (simple-array (signed-byte 32) (*)) :read-only t)
  (foreign-ctx-ptr nil :type (or null cffi:foreign-pointer))    ;; Transient / Non-serializable
  (logits-cache    #() :type (simple-array single-float (*))     :read-only t))

4.2 Canonical S-Expression Format (Purged of Foreign Memory)
;; Semantic State:
;; (:semantic-state
;;   :id "sem-9001"
;;   :projection-id "proj-5501"
;;   :tokens #(1 512 8092)
;;   :logits-sample-top3 #((:token 42 :logit 12.5) (:token 99 :logit 10.1)))

// =============================================================================

# SECTION 5: PHASE D - RELATIONAL GRAPH (G) STRUCTURES

5.1 Common Lisp Definition
(defstruct (graph-node
            (:constructor make-graph-node)
            (:conc-name node-)
            (:type list))
  (id         ""  :type string)
  (label      ""  :type string)
  (properties nil :type list)) ;; Alist

(defstruct (graph-edge
            (:constructor make-graph-edge)
            (:conc-name edge-)
            (:type list))
  (source   ""  :type string)
  (target   ""  :type string)
  (relation :associated-with :type symbol)
  (weight   1.0 :type single-float))

(defstruct (relational-graph
            (:constructor make-relational-graph)
            (:conc-name graph-)
            (:copier nil))
  (id    ""  :type uuid-string :read-only t)
  (nodes nil :type list        :read-only t) ;; List of graph-node
  (edges nil :type list        :read-only t)) ;; List of graph-edge

5.2 Canonical S-Expression Format
;; Relational Graph:
;; (:graph
;;   :id "grp-3301"
;;   :nodes ((:node :id "n1" :label "ConceptA" :properties ((:type . :entity)))
;;           (:node :id "n2" :label "ConceptB" :properties ((:type . :action))))
;;   :edges ((:edge :source "n1" :target "n2" :relation :causes :weight 0.95)))

// =============================================================================

# SECTION 6: PHASE E - OBSERVATION (O) STRUCTURES

6.1 Common Lisp Definition
(defstruct (observation-report
            (:constructor make-observation-report)
            (:conc-name obs-)
            (:copier nil))
  (id            ""  :type uuid-string :read-only t)
  (graph-id      ""  :type uuid-string :read-only t)
  (anomalies     nil :type list        :read-only t) ;; List of (:anomaly-type . description)
  (causal-loops  nil :type list        :read-only t) ;; List of node-id paths
  (coherency-score 1.0 :type single-float :read-only t))

6.2 Canonical S-Expression Format
;; Observation Report:
;; (:observation-report
;;   :id "obs-7701"
;;   :graph-id "grp-3301"
;;   :anomalies ((:unresolved-reference . "Node n3 missing target"))
;;   :causal-loops (("n1" "n2" "n1"))
;;   :coherency-score 0.88)

// =============================================================================

# SECTION 7: PHASE F - BOUNDARY INLET (C) STRUCTURES

7.1 Common Lisp Definition
(defstruct (external-rep
            (:constructor make-external-rep)
            (:conc-name ext-rep-))
  (raw-bytes   #() :type (simple-array (unsigned-byte 8) (*)))
  (encoding    :utf-8 :type symbol)
  (received-at 0   :type timestamp))

(defstruct (normalized-rep
            (:constructor make-normalized-rep)
            (:conc-name norm-rep-)
            (:copier nil))
  (id         ""   :type uuid-string :read-only t)
  (parsed-sexp nil :type t          :read-only t) ;; Pure S-expression tree
  (valid-p    t    :type boolean    :read-only t))

7.2 Canonical S-Expression Format
;; Normalized Boundary Inlet Representation:
;; (:normalized-rep
;;   :id "norm-001"
;;   :valid-p t
;;   :parsed-sexp (:command :action "INFER" :payload "Compute next step"))

// =============================================================================

# SECTION 8: SERIALIZATION GENERIC INTERFACE

8.1 Generic Protocol Signatures
(defgeneric to-sexp (object)
  (:documentation "Converts a Chron-LLM structure into a canonical, portable S-expression."))

(defgeneric from-sexp (sexp type-specifier)
  (:documentation "Parses a canonical S-expression and restores the corresponding CL structure."))