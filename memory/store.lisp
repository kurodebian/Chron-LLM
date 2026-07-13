(defpackage :chron-r2-0-a
  (:use :cl)
  (:export
   #:payload-ref #:payload-ref-p #:make-payload-ref #:payload-ref-hash
   #:payload-ref-type #:payload-ref-size #:payload-ref-storage
   #:make-memory-store #:store-payload #:load-payload #:payload-exists-p
   #:causal-node #:causal-node-p #:make-causal-node #:causal-node-id
   #:causal-node-type #:causal-node-payload-ref #:causal-node-metadata
   #:causal-edge #:causal-edge-p #:make-causal-edge #:causal-edge-from
   #:causal-edge-to #:causal-edge-type
   #:causal-graph #:causal-graph-p #:make-causal-graph #:causal-graph-nodes
   #:causal-graph-edges #:add-node! #:add-edge! #:get-node
   #:causal-subgraph #:associated-evaluations
   #:context-node #:context-node-p #:make-context-node #:context-node-id
   #:context-node-type #:context-node-content #:context-node-feedbacks
   #:project-context
   #:prefill-state #:prefill-state-p #:make-prefill-state #:prefill-state-context
   #:prefill-state-target-id #:prefill-state-hash #:build-prefill-state
   #:canonical-prompt #:sha256-string
   ;; R2.0-B World Runtime
   #:world #:world-p #:world-id #:world-graph-ref #:world-memory-ref
   #:world-root-node #:world-head-node #:world-projection-policy #:world-metadata
   #:world-lifecycle #:make-world #:fork-world #:replace-world-metadata!
   #:kernel-commit-world! #:replay-world
   #:world-registry #:world-registry-p #:make-world-registry #:register-world
   #:find-world #:active-world #:set-active-world #:list-worlds #:archive-world))

(in-package :chron-r2-0-a)

(defstruct (payload-ref (:constructor make-payload-ref (hash type size storage)))
  (hash "" :type string :read-only t)
  (type :text :type keyword :read-only t)
  (size 0 :type (integer 0 *) :read-only t)
  (storage :memory :type keyword :read-only t))

;;; A store is deliberately an explicit value.  Nothing in this module consults
;;; a process-global cache, which keeps content addressing reproducible.
(defun make-memory-store ()
  (make-hash-table :test #'equal))

(defun utf8-octets (string)
  (let ((bytes (make-array 0 :element-type '(unsigned-byte 8)
                           :adjustable t :fill-pointer 0)))
    (labels ((emit (byte) (vector-push-extend byte bytes)))
      (loop for char across string
            for code = (char-code char)
            do (cond ((<= code #x7f) (emit code))
                     ((<= code #x7ff) (emit (logior #xc0 (ash code -6)))
                                      (emit (logior #x80 (logand code #x3f))))
                     ((<= code #xffff) (emit (logior #xe0 (ash code -12)))
                                       (emit (logior #x80 (logand (ash code -6) #x3f)))
                                       (emit (logior #x80 (logand code #x3f))))
                     (t (emit (logior #xf0 (ash code -18)))
                        (emit (logior #x80 (logand (ash code -12) #x3f)))
                        (emit (logior #x80 (logand (ash code -6) #x3f)))
                        (emit (logior #x80 (logand code #x3f)))))))
    bytes))

(defun %u32 (integer) (logand integer #xffffffff))
(defun %ror (integer count)
  (logior (ash integer (- count)) (ash integer (- 32 count))))
(defparameter +sha256-k+
  #(#x428a2f98 #x71374491 #xb5c0fbcf #xe9b5dba5 #x3956c25b #x59f111f1 #x923f82a4 #xab1c5ed5
    #xd807aa98 #x12835b01 #x243185be #x550c7dc3 #x72be5d74 #x80deb1fe #x9bdc06a7 #xc19bf174
    #xe49b69c1 #xefbe4786 #x0fc19dc6 #x240ca1cc #x2de92c6f #x4a7484aa #x5cb0a9dc #x76f988da
    #x983e5152 #xa831c66d #xb00327c8 #xbf597fc7 #xc6e00bf3 #xd5a79147 #x06ca6351 #x14292967
    #x27b70a85 #x2e1b2138 #x4d2c6dfc #x53380d13 #x650a7354 #x766a0abb #x81c2c92e #x92722c85
    #xa2bfe8a1 #xa81a664b #xc24b8b70 #xc76c51a3 #xd192e819 #xd6990624 #xf40e3585 #x106aa070
    #x19a4c116 #x1e376c08 #x2748774c #x34b0bcb5 #x391c0cb3 #x4ed8aa4a #x5b9cca4f #x682e6ff3
    #x748f82ee #x78a5636f #x84c87814 #x8cc70208 #x90befffa #xa4506ceb #xbef9a3f7 #xc67178f2))

(defun sha256-string (string)
  "Return the canonical sha256: hexadecimal address for STRING's UTF-8 bytes."
  (let* ((source (utf8-octets string)) (bits (* 8 (length source)))
         (padded (make-array (+ (length source) 1 8)
                             :element-type '(unsigned-byte 8) :initial-element 0)))
    (replace padded source) (setf (aref padded (length source)) #x80)
    (let* ((length-with-zeroes (* 64 (ceiling (length padded) 64)))
           (data (adjust-array padded length-with-zeroes :initial-element 0)))
      (loop for index from 0 below 8
            do (setf (aref data (+ (- length-with-zeroes 8) index))
                     (ldb (byte 8 (* 8 (- 7 index))) bits)))
      (let ((h (vector #x6a09e667 #xbb67ae85 #x3c6ef372 #xa54ff53a
                       #x510e527f #x9b05688c #x1f83d9ab #x5be0cd19)))
        (loop for offset from 0 below length-with-zeroes by 64 do
          (let ((w (make-array 64 :initial-element 0)))
            (loop for i below 16 do
              (setf (aref w i) (logior (ash (aref data (+ offset (* i 4))) 24)
                                        (ash (aref data (+ offset (* i 4) 1)) 16)
                                        (ash (aref data (+ offset (* i 4) 2)) 8)
                                        (aref data (+ offset (* i 4) 3)))))
            (loop for i from 16 below 64 do
              (setf (aref w i) (%u32 (+ (aref w (- i 16))
                                         (logxor (%ror (aref w (- i 15)) 7)
                                                 (%ror (aref w (- i 15)) 18)
                                                 (ash (aref w (- i 15)) -3))
                                         (aref w (- i 7))
                                         (logxor (%ror (aref w (- i 2)) 17)
                                                 (%ror (aref w (- i 2)) 19)
                                                 (ash (aref w (- i 2)) -10))))))
            (let ((a (aref h 0)) (b (aref h 1)) (c (aref h 2)) (d (aref h 3))
                  (e (aref h 4)) (f (aref h 5)) (g (aref h 6)) (hh (aref h 7)))
              (loop for i below 64 do
                (let* ((s1 (logxor (%ror e 6) (%ror e 11) (%ror e 25)))
                       (choice (logxor (logand e f) (logand (lognot e) g)))
                       (t1 (%u32 (+ hh s1 choice (aref +sha256-k+ i) (aref w i))))
                       (s0 (logxor (%ror a 2) (%ror a 13) (%ror a 22)))
                       (majority (logxor (logand a b) (logand a c) (logand b c)))
                       (t2 (%u32 (+ s0 majority))))
                  (setf hh g g f f e e (%u32 (+ d t1)) d c c b b a a (%u32 (+ t1 t2)))))
              (loop for i below 8 for value in (list a b c d e f g hh)
                    do (setf (aref h i) (%u32 (+ (aref h i) value)))))))
        (format nil "sha256:~{~8,'0X~}" (coerce h 'list))))))

(defun %content-string (content)
  (if (stringp content) content
      (with-standard-io-syntax (prin1-to-string content))))

(defun store-payload (store content &key (type :text) (storage :memory))
  (let* ((text (%content-string content)) (hash (sha256-string text))
         (entry (gethash hash store)))
    (unless entry (setf (gethash hash store) text))
    (make-payload-ref hash type (length (utf8-octets text)) storage)))

(defun load-payload (store reference)
  (gethash (if (payload-ref-p reference) (payload-ref-hash reference) reference) store))

(defun payload-exists-p (store reference)
  (nth-value 1 (gethash (if (payload-ref-p reference) (payload-ref-hash reference) reference) store)))
