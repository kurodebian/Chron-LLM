(defpackage :chronos-r1
  (:use :cl)
  (:export
   ;; domain
   #:event #:event-p #:make-event #:event-id #:event-source #:event-payload
   #:event-metadata #:candidate #:candidate-p #:make-candidate #:candidate-id
   #:candidate-source #:candidate-trigger #:candidate-intent #:candidate-payload
   #:candidate-constraints #:candidate-metadata
   #:canonical #:canonical-p #:make-canonical #:canonical-history #:canonical-config
   #:canonical-memory-ref #:canonical-clock
   #:kernel-state #:make-kernel-state #:kernel-state-canonical
   #:kernel-state-deferred-queue #:kernel-state-working #:kernel-state-faults
   #:validation-report #:validation-report-p #:validation-report-candidate-id
   #:validation-report-syntax-violations #:validation-report-semantic-violations
   #:validation-report-invariant-violations #:validation-report-observations
   #:runtime-command #:runtime-command-p #:runtime-command-kind #:runtime-command-data
   ;; pure operations
   #:derive #:replay #:build-prompt #:validate #:policy-router #:recover
   ;; authoritative boundary and state machine
   #:commit #:kernel-transition #:wake-deferred #:branch-worldline
   ;; reference runtime facade
   #:make-runtime #:runtime-p #:runtime-state #:runtime-next-candidate-id
   #:runtime-submit #:runtime-run-candidate #:runtime-run-backend
   #:runtime-last-command #:chronos-r1-self-test))
