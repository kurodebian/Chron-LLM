# Chron-LLM Phase E Specification
## IR to Causal DSL Transformation Contract v1.0

Status: Design Frozen Baseline
Layer: Phase E Translation Layer
Scope:
IR Stream → Causal DSL → Candidate
Relation:
Upstream: R1 IR Observation Layer
Downstream: R1 Causal Kernel
Phase-E の役割定義

Phase-E の責務は：

非権威的な推論観測（IR）を、Kernel が評価可能な因果操作表現（DSL）へ正規化すること

である。

重要なのは：

Phase-E は判断しない

行わない：

commit判断
rollback判断
retry判断
世界線選択

行う：

構造化
正規化
因果操作への変換
Architecture Position

正式な流れ：

llama.cpp
    |
    v
Physical Event
    |
    v
IR Stream
    |
    v
Phase E
IR → Causal DSL
    |
    v
Candidate
    |
    v
Validation
    |
    v
Policy Router
    |
    v
Kernel Transition
    |
    v
Canonical
DSL Design Principle

DSL は Lisp S-expression を採用する。

理由：

Chron-LLM 自体が Common Lisp Kernel であり、

parser不要
macro拡張可能
debug容易
immutable dataとして扱える

ため。

Causal DSL Core Syntax v1.0
1. EMIT

生成イベント。

(emit
 :token 1532
 :position 42
 :confidence 0.83)

意味：

LLMがtokenを生成した

ただし：

正史ではない
Candidate生成用データ
2. OBSERVE

観測結果。

(observe
 :type :stagnation
 :score 0.91)

例：

(observe
 :type :divergence
 :score 0.42)

用途：

Phase G → Phase E → Kernel

の情報伝達。

3. PROPOSE

Candidate化。

(propose
 :intent :append
 :payload "生成文章")

これは：

DSL
 ↓
Candidate

への境界。

4. BRANCH

世界線候補生成。

(branch
 :causal-id "world-02"
 :parent "world-01")

意味：

新しい可能世界を作る。

注意：

branchしただけではCanonical変更なし。

5. COMMIT

これはDSL内では予約命令。

(commit
 :intent :append)

ただし：

Phase Eでは発行禁止。

理由：

commit権限はKernelのみ。

正式ルール：

DSL COMMIT
    |
    v
Candidate metadata
    |
    v
Policy Router
    |
    v
Kernel Commit
DSL Data Model
(defstruct causal-op
  type
  payload
  metadata)

例：

(make-causal-op
 :type :emit
 :payload token
 :metadata
 '(:pos 12))
IR → DSL Mapping
IR
(ir
 :pos 10
 :phase 1
 :token 534
 :score 0.7)

↓

DSL
(emit
 :token 534
 :position 10
 :confidence 0.7)
Translation Contract
translate-ir-stream(ir-stream)

保証：

Deterministic

同一IR:

IR A

は必ず：

DSL A

になる。

Loss Controlled

Phase E は情報を勝手に破棄しない。

保持：

token
position
phase
score
causal metadata
Non-authoritative

DSL生成では：

Canonical変更禁止。

Candidate Integration

変換後：

Causal DSL

      |
      v

Candidate

      |
      v

ValidationReport

      |
      v

PolicyRouter

      |
      v

Commit
Translation Boundary

Frozen:

DSL opcode
operand形式
IR→DSL deterministic mapping
Candidate変換契約

Flexible:

detector種類
semantic extractor
scoring model
optimization
最重要設計制約

Phase-E は「意味理解器」ではない。

つまり：

誤った設計:

IR
 |
AI解析
 |
意味判断
 |
DSL

ではない。

正しい設計:

IR
 |
構造抽出
 |
正規化
 |
DSL
 |
Kernel判断

である。

意味判断は Kernel Policy または将来の Semantic Layer の責務。

Chron-LLM 最終レイヤ構造
                 LLM

                  |
                  v

        Physical Event Stream

                  |
                  v

          R1 Observation

                  |
                  v

             Phase E
       IR → Causal DSL

                  |
                  v

          R1 Runtime Core

                  |
                  v

          Causal Kernel

                  |
                  v

             Canonical

                  |
                  v

             Worldline
最終評価

Phase-E の設計方針は以下で凍結するのが適切。

DSL = S式
Phase-E = 翻訳のみ
commit権限なし
Candidate生成まで担当
Kernelが因果判断を担当

この境界を守れば、Chron-LLM は「LLMの内部状態を操作するシステム」ではなく、

観測 → 正規化 → 因果評価 → 権威状態更新

という決定的ランタイムとして成立する。