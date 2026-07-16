# Chron-LLM R2.0-B 仕様書

## World Registry Runtime Specification

---

# 1. 概要

## 目的

本モジュールは **World Registry** を提供する。

World Registry は Chron-LLM において

> **世界線(World)そのものを管理するものではなく、
> 世界線への参照(View)を登録・管理するサービス**

である。

Truth（Graph・Memory）は一切変更せず、

* Worldの登録
* Active World管理
* World探索
* 世界線の親子関係
* Archive管理

のみを担当する。

---

# 2. 設計責務

## Responsibility

World Registry は

* World登録
* World検索
* Active World管理
* World一覧
* World親子関係
* Lifecycle管理

のみ担当する。

---

## Non Responsibility

World Registry は一切以下を行わない。

* Graph生成
* Node生成
* Edge生成
* Memory保存
* Projection
* Replay
* Commit
* Branch生成
* Payload保存

---

# 3. データ構造

```lisp
(defstruct world-registry ...)
```

Registryは以下を保持する。

| スロット      | 内容              |
| --------- | --------------- |
| worlds    | World一覧         |
| ancestry  | 親子関係            |
| active-id | 現在のActive World |
| graph     | 共有Graph         |
| memory    | 共有Memory        |

---

## worlds

```
(world-id . world)
```

のAssociation List。

登録順を保持する。

例

```
((0 . world0)
 (1 . world1)
 (2 . world2))
```

---

## ancestry

```
(child-id . parent-id)
```

を保持する。

例

```
(1 . 0)
(2 . 1)
```

---

## active-id

現在利用中の世界線。

```
NIL
```

なら未選択。

---

## graph

全Worldが共有するGraph。

Registry登録後は変更不可。

---

## memory

全Worldが共有するPayload Store。

---

# 4. World検索

## find-world

```
(find-world registry world-id)
```

---

### 入力

* Registry
* World ID

---

### 処理

Association Listから検索する。

```
assoc
```

利用。

---

### 出力

存在

```
World
```

存在しない

```
NIL
```

---

# 5. World一覧

```
(list-worlds registry)
```

登録順にWorld一覧を返す。

内部では

```
mapcar #'cdr
```

のみ。

---

# 6. Active World取得

```
(active-world registry)
```

---

### 処理

```
active-id
↓

find-world
```

---

### 戻り値

```
World
```

または

```
NIL
```

---

# 7. Shared Object検証

内部関数

```
%registry-shared-objects-p
```

---

## 目的

登録されるWorldが

Graph

Memory

を共有しているか確認する。

---

判定条件

```
(eq graph)
```

```
(eq memory)
```

である。

つまり

**物理的同一オブジェクト**

でなければならない。

---

# 8. World登録

```
(register-world ...)
```

---

## 目的

RegistryへWorldを登録する。

Truthは変更しない。

コメントにも

```
indexes views
never changes truth
```

と記載されている。

---

## 引数

```
registry
world
parent-id(optional)
```

---

## 登録手順

### ① 型確認

```
(world-p world)
```

で確認。

失敗

```
Only a world may be registered.
```

---

### ② ID重複確認

```
(find-world ...)
```

で検索。

重複時

```
World id has already been used
```

---

### ③ Graph共有確認

```
%registry-shared-objects-p
```

---

共有されていない場合

```
Every registered world
must share
the canonical graph
and memory.
```

---

### ④ Parent存在確認

parent-id指定時

```
find-world
```

失敗

```
Parent world must already be registered.
```

---

### ⑤ Registry初期化

初登録時のみ

```
graph
memory
```

をWorldから取得。

---

### ⑥ worlds追加

```
append
```

で末尾追加。

登録順保持。

---

### ⑦ ancestry追加

parent指定時

```
(child . parent)
```

追加。

---

### ⑧ World返却

登録したWorldを返す。

---

# 9. Active World変更

```
(set-active-world ...)
```

---

## 手順

### ① 対象検索

```
find-world
```

存在しない

```
Unknown world id
```

---

### ② Archive確認

```
:archived
```

は禁止。

```
Archived worlds cannot become active.
```

---

### ③ 現在World更新

現在Activeが存在し

変更対象と異なる場合

```
:inactive
```

へ変更。

内部関数

```
%set-world-lifecycle!
```

利用。

---

### ④ 新World更新

```
:active
```

へ変更。

---

### ⑤ Active ID更新

```
active-id
```

変更。

---

### ⑥ World返却

---

# 10. Archive

```
(archive-world ...)
```

---

## 手順

① World取得

↓

② 存在確認

↓

③ Lifecycle

```
:archived
```

へ変更

↓

④ Activeなら解除

```
active-id=nil
```

↓

⑤ World返却

---

# 11. Lifecycle遷移

本コードから読み取れる状態は

```
            register
               │
               ▼
         +-------------+
         | inactive    |
         +-------------+
             ▲     │
             │     │ set-active
             │     ▼
         +-------------+
         | active      |
         +-------------+
               │
               │ archive
               ▼
         +-------------+
         | archived    |
         +-------------+
```

ArchivedからActiveへの復帰は禁止。

---

# 12. データ不変条件（Invariants）

Registryは常に以下を保証する。

### I-1

World IDは一意。

---

### I-2

登録順保持。

---

### I-3

全Worldは同じGraph共有。

---

### I-4

全Worldは同じMemory共有。

---

### I-5

Parentは必ず登録済。

---

### I-6

Activeは最大1つ。

---

### I-7

ArchivedはActiveになれない。

---

# 13. 時間計算量

| API              | 計算量                           |
| ---------------- | ----------------------------- |
| find-world       | O(n)                          |
| list-worlds      | O(n)                          |
| active-world     | O(n)                          |
| register-world   | O(n)（`append`・`assoc`による線形探索） |
| set-active-world | O(n)                          |
| archive-world    | O(n)                          |

**備考:** `worlds` と `ancestry` は Association List として実装されているため、検索・追加は線形時間となる。大量の World を扱う将来フェーズではハッシュテーブル等への置き換えが性能改善候補となる。

---

# 14. モジュール間の位置づけ

```
                Kernel
                   │
                   ▼
        World Registry（本仕様）
           │              │
           ▼              ▼
       World View     Active管理
           │
           ▼
      Shared Graph
      Shared Memory
```

World Registry は **Truth（Graph・Memory）の所有者ではなく、それらを共有する World インスタンスの登録・ライフサイクル管理を担うレイヤ**として設計されている。これにより、世界線の切り替えや管理を行っても、基盤となる因果グラフや永続メモリの一貫性は維持される。
