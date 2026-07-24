(in-package :experiment)

;; アトラクター構造（仕様書 v0.2 定義）
(defstruct attractor
  attractor-id    ; 識別子 (cycle / terminal-point)
  type            ; cycle / fixed-point
  nodes           ; (list of node-id) 代表ノード
  stability       ; 安定性スコア
  recurrence      ; 再帰頻度
  )

;; Basin Analysis Result（仕様書 v0.2 定義）
(defstruct basin-analysis-result
  basins          ; (list of basin)
  total-attractors ; 総アトラクター数
  convergence-rate; 収束率統計
  )

(defun build-basin-map (graph nodes steps &optional convergence-threshold)
  "Build a map of attractors to their basins."
  (let ((table (make-hash-table)))
    (dolist (n nodes)
      (let ((a (find-attractor graph n steps convergence-threshold)))
        (push n (gethash a table))))
    table))

(defun build-basin-structure (basin-map total-nodes)
  "Construct basin structures from the given map."
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
    ;; 結果を構造体として返す
    (make-basin-analysis-result
     :basins (nreverse result)
     :total-attractors (hash-table-count basin-map)
     :convergence-rate (/ total-nodes total-nodes)))
  )
