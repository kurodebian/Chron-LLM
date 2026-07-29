MODULE chronos-r0.chat
DEPS history, prompt, llama, trace

TYPE Session = { model: ModelRef | Nil, history: History }
TYPE Event = { role: 'user' | 'assistant', content: Str }
TYPE Trace = { user-text: Str, prompt: Str, raw: Str, parsed: Str, h-before: Snap, h-after: Snap, p-len: Int, r-len: Int, hs-b: Int, hs-a: Int }

OP make-new-session(model?: ModelRef) -> Session
  RETURN { model: model | default(), history: history.make-history() }

OP extract-generation(raw: Str) -> Str = raw

OP make-assistant-event(text: Str) -> Event = { role: 'assistant', content: text }

OP chat(session: Session, user-text: Str) -> Session
  h = session.history
  snap-b = history.snapshot(h)
  history.append-user(h, user-text)
  prompt = prompt.project-to-prompt(h)
  raw = llama.llama-run(prompt)
  parsed = extract-generation(raw)
  history.append-event(h, make-assistant-event(parsed))
  snap-a = history.snapshot(h)
  trace.log({ user-text: user-text, prompt: prompt, raw: raw, parsed: parsed, h-before: snap-b, h-after: snap-a, p-len: len(prompt), r-len: len(parsed), hs-b: size(snap-b), hs-a: size(snap-a) })
  RETURN session

OP start-chat() -> Void
  sess = make-new-session()
  LOOP {
    PRINT "You>"
    inp = read-line()
    IF inp == EOF | ":exit" BREAK
    chat(sess, inp)
    evt = history.find-last-role(sess.history, 'assistant')
    IF evt != Nil PRINT "AI> " + evt.content
  }

INV Session.fields == { model, history }
INV chat.seq: append-user -> project-prompt -> llama-run -> append-assistant
INV trace.snapshots: h-before AND h-after present