MODULE llama-agent.lisp : Bootloader
TYPE Layer = Physical | Logical | Kernel | Immune | Runtime | Generation | MainLoop
STATE *system-dir* := uiop:pathname-directory-pathname(*load-pathname*)
STATE *use-mock-physical-p* : Bool := T

OP init_quicklisp(): load("quicklisp/setup.lisp") ON_FAIL error()
OP load_libs(): load(["CFFI", "Babel"])
OP load_system_file(f): p:=make-pathname(:directory *system-dir*, :name f); IF probe-file(p) THEN load(p) ELSE warn()

SEQ boot_order := [Physical, Logical, Kernel, Immune, Runtime, Generation, MainLoop]

OP init_layers():
  phys := IF *use-mock-physical-p* THEN "ffi-bindings-mock.lisp" ELSE "ffi-bindings.lisp"
  load_system_file(phys)
  load_system_file("chron-llm.lisp")
  load_system_file("chron-llm-causal.lisp")
  load_system_file("immune-system.lisp")
  load_system_file("chron-llm-runtime.lisp")
  load_system_file("generate.lisp")
  load_system_file("run-test.lisp")

OP start-delta3(path := "/path/to/model.gguf"):
  m := my-llama-model-load(path)
  c := my-llama-init(4096)
  agent-main-loop(c, m)

OP start-delta3-stub():
  PRE *use-mock-physical-p* == T
  agent-main-loop(nil, nil)

INV boot_seq: load_sequence == boot_order
INV abi: sig(my-llama-*_mock) == sig(my-llama-*_real)
INV purity: post_boot_state(bootloader) == {}
INV deps: Layer[i] -> Layer[j] IMPLIES i > j