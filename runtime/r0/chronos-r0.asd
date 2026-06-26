(asdf:defsystem :chronos-r0
  :serial t
  :components
  ((:file "package")
   (:file "history")
   (:file "prompt")
   (:file "llama-run")
   (:file "trace")
   (:file "chat-loop")
   (:file "api")))   ; ← ここで chronos-r0:start-chat が定義される
