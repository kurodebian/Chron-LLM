CONST:
  MAGIC = 'CHWA'
  VERSION = 0x0201
  HDR_SZ = 48
  ALIGN = 8
  READ_EVAL = nil

TYPE:
  Header = {
    magic: u32,
    version: u16,
    type: u8,
    flags: u8,
    txid: u64,
    clock: u64,
    target_hash_hi: u64,
    target_hash_lo: u64,
    payload_len: u32,
    reserved: u32
  }
  Record = {
    hdr: Header,
    payload: [u8][hdr.payload_len],
    crc: u32,
    pad: [u8][0..7]
  }
  TxState = IDLE | PREPARED | COMMITTED | ABORTED
  Status = OK | CORRUPT | TRUNCATED
  Result = (data: any, tag: Status)

INV:
  INV_HDR_SZ: sizeof(Header) == 48
  INV_HDR_ALIGN: offset(Header.u64_field) % 8 == 0
  INV_REC_ALIGN: sizeof(Record) % 8 == 0
  INV_NO_ERR: !raise(LispError)
  INV_SAFE_READ: *read-eval* == nil

STATE:
  lock: Mutex
  state: TxState = IDLE

OP: prepare(txid, payload) -> Result
  PRE: state == IDLE
  ACQUIRE lock
  rec = Record { hdr: { type: PREPARED, txid: txid, payload_len: len(payload) }, payload: payload }
  write(rec)
  fdatasync()
  state = PREPARED
  RELEASE lock
  POST: state == PREPARED
  RETURN (rec, OK)

OP: commit(txid) -> Result
  PRE: state == PREPARED
  ACQUIRE lock
  rec = Record { hdr: { type: COMMITTED, txid: txid } }
  write(rec)
  fdatasync()
  apply_sm()
  state = COMMITTED
  RELEASE lock
  POST: state == COMMITTED
  RETURN (rec, OK)

OP: abort(txid) -> Result
  PRE: state == PREPARED
  ACQUIRE lock
  rec = Record { hdr: { type: ABORTED, txid: txid } }
  write(rec)
  fdatasync()
  state = ABORTED
  RELEASE lock
  POST: state == ABORTED
  RETURN (rec, OK)

OP: recover() -> Result
  SCAN recs
  FOR r IN recs:
    IF !crc_ok(r) OR torn(r):
      TRUNCATE(r.off)
      RETURN (nil, TRUNCATED)
    CASE r.hdr.type:
      PREPARED:
        IF !has(COMMITTED) AND !has(ABORTED):
          abort(r.hdr.txid)
          state = ABORTED
      COMMITTED:
        apply_sm(r)
        state = COMMITTED
      ABORTED:
        state = ABORTED
  RETURN (nil, OK)