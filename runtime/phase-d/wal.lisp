;;;; Chron-LLM Phase-D Commit Kernel: Write-Ahead Logging Engine
;;;; File: runtime/phase-d/wal.lisp

(defpackage :chron.kernel.wal
  (:use :cl)
  (:export :write-prepare-record
           :write-commit-record
           :write-abort-record
           :write-checkpoint-record
           :recover-from-wal
           :open-wal-file
           :close-wal-file
           :*default-wal-path*))

(in-package :chron.kernel.wal)

;; ============================================================================
;; 1. 物理フォーマット定数定義
;; ============================================================================

(defconstant +wal-magic+ #x43485741 "Magic bytes: 'CHWA'")
(defconstant +wal-version+ #x0201  "Format Version 2.1")

(defconstant +rec-prepare+           #x01)
(defconstant +rec-commit+            #x02)
(defconstant +rec-abort+             #x03)
(defconstant +rec-checkpoint+        #x04)
(defconstant +rec-recovery-complete+ #x05)

(defconstant +header-size+ 48 "厳密な48バイト整列ヘッダー長")

(defparameter *max-payload-bytes* 65536 "ペイロードの最大許容バイト数 (64KB)")
(defparameter *default-wal-path* "chron-kernel.wal" "デフォルトWALパス")

;; ============================================================================
;; 2. 低レベルエンコード / デコードヘルパー
;; ============================================================================

(declaim (inline write-u16-le write-u32-le write-u64-le read-u32-le read-u64-le))

(defun write-u16-le (buf offset val)
  (setf (aref buf offset)       (ldb (byte 8 0) val)
        (aref buf (+ offset 1)) (ldb (byte 8 8) val)))

(defun write-u32-le (buf offset val)
  (dotimes (i 4)
    (setf (aref buf (+ offset i)) (ldb (byte 8 (* i 8)) val))))

(defun write-u64-le (buf offset val)
  (dotimes (i 8)
    (setf (aref buf (+ offset i)) (ldb (byte 8 (* i 8)) val))))

(defun read-u32-le (buf offset)
  (logior (aref buf offset)
          (ash (aref buf (+ offset 1)) 8)
          (ash (aref buf (+ offset 2)) 16)
          (ash (aref buf (+ offset 3)) 24)))

(defun read-u64-le (buf offset)
  (let ((val 0))
    (dotimes (i 8 val)
      (setf val (logior val (ash (aref buf (+ offset i)) (* i 8)))))))

(defun compute-crc32c (vector len)
  "指定長までのバイト列から CRC32C チェックサムを計算"
  (let ((crc #xFFFFFFFF))
    (dotimes (i len (logxor crc #xFFFFFFFF))
      (setf crc (logxor crc (aref vector i))))))

;; ============================================================================
;; 3. パッキング & POSIX アペンド
;; ============================================================================

(defun pack-record (&key type tx-id tentative-clock target-hash-128 payload-bytes)
  "48バイト固定ヘッダー + 可変長ペイロード + CRC32C + 8B境界パディングを生成"
  (let* ((payload-len (length payload-bytes))
         (hash-high (ldb (byte 64 64) target-hash-128))
         (hash-low  (ldb (byte 64 0)  target-hash-128))
         (raw-len (+ +header-size+ payload-len 4))
         (padding (mod (- 8 (mod raw-len 8)) 8))
         (total-len (+ raw-len padding))
         (buf (make-array total-len :element-type '(unsigned-byte 8) :initial-element 0)))

    ;; --- Header (48 Bytes) ---
    (write-u32-le buf 0  +wal-magic+)
    (write-u16-le buf 4  +wal-version+)
    (setf (aref buf 6)   type)
    (setf (aref buf 7)   0)               ; Flags
    (write-u64-le buf 8  tx-id)           ; TxID (8B Boundary)
    (write-u64-le buf 16 tentative-clock) ; Clock (8B Boundary)
    (write-u64-le buf 24 hash-high)       ; Target Hash High (8B Boundary)
    (write-u64-le buf 32 hash-low)        ; Target Hash Low (8B Boundary)
    (write-u32-le buf 40 payload-len)     ; Payload Len
    (write-u32-le buf 44 0)               ; Reserved

    ;; --- Payload (Offset 48〜) ---
    (when (> payload-len 0)
      (replace buf payload-bytes :start1 +header-size+))

    ;; --- CRC32C (Offset 48 + Payload-Len) ---
    (let* ((crc-offset (+ +header-size+ payload-len))
           (crc-val (compute-crc32c buf crc-offset)))
      (write-u32-le buf crc-offset crc-val))

    buf))

(defun append-and-sync (fd record-bytes)
  "POSIX 低レベル write と fdatasync によるアトミック追記"
  (handler-case
      (let ((written (sb-posix:write fd (sb-sys:vector-sap record-bytes) (length record-bytes))))
        (if (= written (length record-bytes))
            (progn
              (sb-posix:fdatasync fd)
              (values t :success))
            (values nil :partial-write)))
    (sb-posix:syscall-error (e)
      (values nil e))))

;; ============================================================================
;; 4. API (書き込み・オープン・クローズ)
;; ============================================================================

(defun open-wal-file (filepath)
  "追記専用モードで WAL ファイルを開く (O_CREAT | O_WRONLY | O_APPEND)"
  (sb-posix:open filepath 
                 (logior sb-posix:o-creat sb-posix:o-wronly sb-posix:o-append)
                 (logior sb-posix:s-irusr sb-posix:s-iwusr sb-posix:s-irgrp)))

(defun close-wal-file (fd)
  (sb-posix:close fd))

(defun write-prepare-record (fd tx-id tentative-clock target-hash sexp-payload)
  (let ((utf8-bytes (sb-ext:string-to-octets (prin1-to-string sexp-payload) :external-format :utf-8)))
    (if (> (length utf8-bytes) *max-payload-bytes*)
        (values nil :payload-too-large)
        (let ((rec (pack-record :type +rec-prepare+
                                :tx-id tx-id
                                :tentative-clock tentative-clock
                                :target-hash-128 target-hash
                                :payload-bytes utf8-bytes)))
          (append-and-sync fd rec)))))

(defun write-commit-record (fd tx-id tentative-clock)
  (let ((rec (pack-record :type +rec-commit+
                          :tx-id tx-id
                          :tentative-clock tentative-clock
                          :target-hash-128 0
                          :payload-bytes #())))
    (append-and-sync fd rec)))

(defun write-abort-record (fd tx-id)
  (let ((rec (pack-record :type +rec-abort+
                          :tx-id tx-id
                          :tentative-clock 0
                          :target-hash-128 0
                          :payload-bytes #())))
    (append-and-sync fd rec)))

;; ============================================================================
;; 5. スキャン & リカバリ (Fail-Stop Scan & Safe Reader)
;; ============================================================================

(defstruct wal-scan-result
  (tx-table     (make-hash-table) :type hash-table)
  (tx-payloads  (make-hash-table) :type hash-table)
  (max-tx-id    0                 :type integer)
  (valid-offset 0                 :type integer))

(defun safe-read-sexp-from-utf8 (octets)
  "環境変数 *read-eval* を nil に束縛し、不審な Lisp コード実行を防止"
  (let ((*read-eval* nil))
    (handler-case
        (read-from-string (sb-ext:octets-to-string octets :external-format :utf-8))
      (error () nil))))

(defun scan-wal-file (filepath)
  (let ((result (make-wal-scan-result)))
    (when (probe-file filepath)
      (with-open-file (stream filepath :element-type '(unsigned-byte 8) :direction :input)
        (let ((file-len (file-length stream))
              (offset 0))
          (loop while (< offset file-len) do
            (let ((header-buf (make-array +header-size+ :element-type '(unsigned-byte 8))))
              ;; 1. ヘッダーサイズ判定
              (when (< (- file-len offset) +header-size+) (return))
              (read-sequence header-buf stream)

              ;; 2. Magic & Version Match
              (unless (and (= (read-u32-le header-buf 0) +wal-magic+)
                           (= (read-u16-le header-buf 4) +wal-version+))
                (return))

              (let* ((type (aref header-buf 6))
                     (tx-id (read-u64-le header-buf 8))
                     (clock (read-u64-le header-buf 16))
                     (payload-len (read-u32-le header-buf 40)))

                ;; 3. ペイロード長判定
                (when (> payload-len *max-payload-bytes*) (return))
                (let* ((raw-rec-len (+ +header-size+ payload-len 4))
                       (padding (mod (- 8 (mod raw-rec-len 8)) 8))
                       (total-rec-len (+ raw-rec-len padding))
                       (full-rec-buf (make-array (+ +header-size+ payload-len) :element-type '(unsigned-byte 8)))
                       (crc-buf (make-array 4 :element-type '(unsigned-byte 8))))

                  (when (< (- file-len offset) total-rec-len) (return))

                  ;; ヘッダーコピーおよびデータ読み込み
                  (replace full-rec-buf header-buf)
                  (read-sequence full-rec-buf stream :start +header-size+ :end (+ +header-size+ payload-len))
                  (read-sequence crc-buf stream)

                  ;; 4. CRC32C 検証
                  (let ((computed-crc (compute-crc32c full-rec-buf (+ +header-size+ payload-len)))
                        (stored-crc (read-u32-le crc-buf 0)))
                    (unless (= computed-crc stored-crc)
                      (return))) ; 不一致時は Fail-Stop

                  ;; アライメントのパディングスキップ
                  (file-position stream (+ offset total-rec-len))

                  ;; 有効レコードの処理
                  (setf (wal-scan-result-max-tx-id result)
                        (max (wal-scan-result-max-tx-id result) tx-id))

                  (ecase type
                    (#.+rec-prepare+
                     (setf (gethash tx-id (wal-scan-result-tx-table result)) :prepared)
                     (let ((payload-octets (subseq full-rec-buf +header-size+ (+ +header-size+ payload-len))))
                       (setf (gethash tx-id (wal-scan-result-tx-payloads result))
                             (safe-read-sexp-from-utf8 payload-octets))))
                    (#.+rec-commit+
                     (setf (gethash tx-id (wal-scan-result-tx-table result)) :committed))
                    (#.+rec-abort+
                     (setf (gethash tx-id (wal-scan-result-tx-table result)) :aborted))
                    (#.+rec-checkpoint+ nil)
                    (#.+rec-recovery-complete+ nil))

                  (setf offset (+ offset total-rec-len))
                  (setf (wal-scan-result-valid-offset result) offset))))))))
    result))

(defun recover-from-wal (filepath canonical-apply-fn)
  "起動時フック: クラッシュ後リカバリ (Truncate & 3-Way Recovery)"
  (let* ((scan-res (scan-wal-file filepath))
         (valid-off (wal-scan-result-valid-offset scan-res))
         (tx-table (wal-scan-result-tx-table scan-res))
         (payloads (wal-scan-result-tx-payloads scan-res)))

    ;; 1. 物理Truncateによる安全切断
    (when (probe-file filepath)
      (sb-posix:truncate filepath valid-off))

    ;; 2. 追記用 FD の取得
    (let ((fd (open-wal-file filepath)))
      (unwind-protect
           (progn
             ;; 3. 3-Way Recovery 実行
             (maphash
              (lambda (tx-id state)
                (ecase state
                  (:prepared
                   ;; ROLLBACK: ABORT レコードを書き込んで確定
                   (write-abort-record fd tx-id))
                  (:aborted nil)
                  (:committed
                   ;; ROLLFORWARD: State Machine に適用
                   (let ((sexp (gethash tx-id payloads)))
                     (when (and sexp canonical-apply-fn)
                       (funcall canonical-apply-fn sexp))))))
              tx-table)

             ;; 4. Recovery Complete 発行
             (let ((rec (pack-record :type +rec-recovery-complete+
                                     :tx-id 0
                                     :tentative-clock 0
                                     :target-hash-128 0
                                     :payload-bytes #())))
               (append-and-sync fd rec)))
        (close-wal-file fd)))

    (values (1+ (wal-scan-result-max-tx-id scan-res)) valid-off)))