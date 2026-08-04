PKG chronos-r0.prompt

TYPE History = { events: [Event] }
TYPE Event = { role: Str, content: Str }
CONST BOS="<|begin_of_text|>" SH_ID="<|start_header_id|>" EH_ID="<|end_header_id|>" SYS_PROMPT="あなたは日本語で丁寧に答えるアシスタントです。"

OP project-to-prompt(h: History) -> Str
  PRE h.events[] valid structure
  INV h immutable; Output Only
  DET f(h)=f(h); NoRand/Time/Env
  ALG
    p = BOS + "\n\n"
    p += SH_ID+"system"+EH_ID+"\n\n"+SYS_PROMPT+"\n"
    FOR e IN h.events DO
      r = to_lower(e.role)
      p += SH_ID+r+EH_ID+"\n\n"+e.content+"\n"
    END
    p += SH_ID+"assistant"+EH_ID
  RET p

DEPS chronos-r0.history { history-events, history-event-role, history-event-content }
COMPLEXITY T:O(N+L) S:O(L)