MODULE: llama-agent2.lisp
TYPE: Integrated Bootloader
VERSION: Chron-LLM Δ3 Phase 1.1

STATE:
  *system-dir*: Path = (uiop:pathname-directory-pathname *load-pathname*)
  *use-mock-physical-p*: Boolean

OPS:
  load-system-file(filename):
    path = merge-pathnames(filename, *system-dir*)
    IF NOT probe-file(path) -> ERROR("Required file not found")
    load(path)

SEQUENCE:
  LOG("Chron-LLM Δ3 Phase 1.1 Bootloader Starting")
  INIT_QUICKLISP()
  LOAD_PHYSICAL()
  LOAD_LLM()
  LOAD_CORE()
  LOAD_GRAPH()
  LOAD_WORLD()
  LOAD_IMMUNE()
  LOAD_RUNTIME()
  LOAD_GENERATION()
  LOAD_TEST()
  LOG("Chron-LLM Δ3 Phase 1.1 Boot Completed")

INIT_QUICKLISP():
  IF NOT probe-file("quicklisp/setup.lisp") -> ERROR("Quicklisp not found")
  load("quicklisp/setup.lisp")
  ql:quickload("cffi")
  ql:quickload("babel")

LOAD_PHYSICAL():
  LOG("Loading Physical Layer")
  IF *use-mock-physical-p* -> load-system-file("ffi-bindings-mock.lisp")
  ELSE -> load-system-file("ffi-bindings.lisp")

LOAD_LLM():
  LOG("Loading LLM Interface")
  load-system-file("chron-llm.lisp")

LOAD_CORE():
  LOG("Loading Core")
  load-system-file("chron-llm-core.lisp")

LOAD_GRAPH():
  LOG("Loading Graph Layer")
  load-system-file("chron-llm-graph.lisp")

LOAD_WORLD():
  LOG("Loading World")
  load-system-file("chron-llm-world.lisp")

LOAD_IMMUNE():
  LOG("Loading Immune")
  load-system-file("chron-llm-immune.lisp")

LOAD_RUNTIME():
  LOG("Loading Runtime")
  load-system-file("chron-llm-runtime.lisp")

LOAD_GENERATION():
  LOG("Loading Generation")
  load-system-file("generate.lisp")

LOAD_TEST():
  LOG("Loading Test Wrapper")
  load-system-file("run-test.lisp")

API:
  start-delta3(model-path="/path/to/model.gguf"):
    load-model(model-path)
    init-context()
    agent-main-loop() [BLOCKING]

  start-delta3-stub():
    agent-main-loop(nil, nil)

INVARIANTS:
  INV_LoadOrder: [Physical, LLM, Core, Graph, World, Immune, Runtime, Generation, Test]
  INV_NoReverseDep: Layers depend only on preceding layers
  INV_PhysicalSwap: Physical Layer is sole swappable unit (Mock/FFI)
  INV_FailFast: Stop on missing files/Quicklisp; No recovery

NON_RESPONSIBILITIES:
  Inference, KV, WAL, Graph Logic, Runtime Logic, Prompt, Event, Memory, Immune Logic

PHASE_1_1_CONSTRAINTS:
  NO ASDF, NO Lazy Load, NO Plugins, NO Versioning, NO Config Files, NO Log Levels, NO Parallel Load, NO Hot Reload