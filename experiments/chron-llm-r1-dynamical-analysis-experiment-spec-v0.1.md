📘 Chron-LLM Experimental Causal Dynamics Model
Formal Graph & Basin Specification v1.0
Status: Experimental / Mathematical Foundation
Scope: Graph Dynamics / SCC / Attractor / Basin / Cycle Detection
Relation:

Upstream: IR Observation Layer

Downstream: Phase‑E (IR → Causal DSL)

Used by: Causal Kernel (Phase D/E/F/G)

1. Purpose（目的）
この実験モジュールは、Chron‑LLM の因果カーネルが扱う

世界線の構造（Graph）

因果遷移（Edges）

再帰的振る舞い（Cycles）

安定点（Attractors）

収束領域（Basins）

強連結成分（SCC）

を形式的に定義するための数学モデルである。

Phase‑E の DSL は、このモデルを 「トークン列 → 因果グラフ」 に写像するための意味論として利用する。

2. Graph Model（グラフモデル）
2.1 Node
lisp
(defstruct node id role)
Fields
Field	Meaning
id	ノード識別子
role	reply / temporal / bridge


2.2 Edge
lisp
(defstruct edge from to relation strength)
Fields
Field	Meaning
from	出発ノード
to	到達ノード
relation	reply / temporal / bridge
strength	遷移の強度（確率・重み）


2.3 Graph
lisp
(defstruct graph nodes edges)
3. Example: 3‑Cluster Graph
A/B/C の3クラスターを持つ典型的な因果遷移モデル。

A: reply cluster（強い循環）

B: temporal cluster（弱い循環）

C: bridge cluster（A/B を接続）

この構造は LLM の生成行動の「局所安定性」や「モード遷移」を模倣する。

4. Dynamics（因果ダイナミクス）
4.1 next-event
lisp
(defun next-event (graph node-id)
node-id から出る edge のうち 最も強い遷移を選択

LLM の「次トークン選択」に相当する

4.2 rollout*
lisp
(defun rollout* (graph start steps)
start ノードから steps 回遷移

LLM の「生成トークン列」を模倣する

4.3 find-attractor
lisp
(defun find-attractor (graph start steps)
rollout の最終ノード

LLM の「最終的に落ち着くモード」を表す

5. Cycle Detection（再帰構造）
5.1 find-cycle
lisp
(defun find-cycle (path)
path の末尾に現れる再帰的サイクルを抽出

LLM の「反復パターン」を検出する

5.2 find-recurrent-cycle
lisp
(defun find-recurrent-cycle (graph start steps)
rollout → cycle 抽出

LLM の「モード循環」を観測する

6. Basin Analysis（収束領域解析）
6.1 build-basin-map
lisp
(defun build-basin-map (graph nodes steps)
各ノードがどの attractor に落ちるかを計測

attractor → basin の対応を構築

6.2 Basin Structure
lisp
(defstruct basin attractor nodes mass ratio)
Meaning
attractor: 収束先

nodes: basin に属するノード

mass: basin の大きさ

ratio: 全体に対する割合

7. SCC（強連結成分）
7.1 compute-sccs
lisp
(defun compute-sccs (graph nodes)
グラフの強連結成分を抽出

LLM の「閉じたモード集合」を特定する

8. Why This Matters for Phase‑E
Phase‑E（IR → Causal DSL）は、
「トークン列を因果グラフとして解釈する」  
という役割を持つ。

この実験モジュールはそのための数学的基盤であり、以下を提供する：

トークン遷移 → グラフ遷移

反復生成 → Cycle

モード安定性 → Attractor

世界線の局所構造 → SCC

世界線の大域構造 → Basin

つまり、Phase‑E の DSL はこのモデルを使って：

IR Stream を「因果グラフの操作列（Causal DSL）」に変換する

という仕様を定義することになる。

Final Statement
この experiments/ モジュールは、
Chron‑LLM の因果カーネルが扱う世界線ダイナミクスの 形式的・数学的基盤である。

Phase‑E の仕様書（chron-llm-phase-e-ir-to-causal-dsl-transformation-contract-v1.0.md）では、
このモデルを DSL の意味論（Semantics）として採用し、
IR → DSL → Kernel の因果パイプラインを完成させる。