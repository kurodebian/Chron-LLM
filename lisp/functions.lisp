;; ============================================================
;; 関数レジストリ（外部ファイル）
;; ============================================================

(setf *function-registry*
  '(("fib" .
     "(defun fib (n)
        (cond
          ((= n 0) 0)
          ((= n 1) 1)
          (t (+ (fib (- n 1)) (fib (- n 2)))))))")

    ("square" .
     "(defun square (x)
        (* x x))")

    ("reverse-list" .
     "(defun reverse-list (lst)
        (labels ((rev (l acc)
                   (if (null l)
                       acc
                       (rev (cdr l) (cons (car l) acc)))))
          (rev lst nil)))")))

