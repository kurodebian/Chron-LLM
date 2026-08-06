import Lake
open Lake DSL

package «ChronKernel» {
  -- Public SDK configuration
}

@[default_target]
lean_lib «ChronKernel» {
  -- 非 TCB 領域向け公開ライブラリターゲット
  roots := #[`ChronKernel]
}

lean_lib «ChronInternal» {
  -- TCB 内部ターゲット (CI 検査対象)
  roots := #[`ChronLLM.Internal]
}