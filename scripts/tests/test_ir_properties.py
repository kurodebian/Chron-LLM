import threading
from hypothesis import given, strategies as st
import pytest

class Phase:
    PREFILL = 0
    GENERATION = 1
    FINALIZE = 2

class IR:
    def __init__(self, ctx_id, pos, phase, token, score):
        self.ctx_id = ctx_id
        self.pos = pos
        self.phase = phase
        self.token = token
        self.score = score
        self._frozen = True

    def __setattr__(self, key, value):
        if getattr(self, '_frozen', False):
            raise AttributeError("INV-IMMUTABLE: IR fields cannot be modified post-creation")
        super().__setattr__(key, value)

class IRBuffer:
    def __init__(self, capacity):
        self.capacity = capacity
        self.size = 0
        self.overflow_count = 0
        self.data = [None] * capacity
        self._lock = threading.Lock()

    def push(self, ir):
        with self._lock:
            slot = self.size
            self.size += 1
            if slot < self.capacity:
                self.data[slot] = ir
                return True
            else:
                self.overflow_count += 1
                return False

    def snapshot(self):
        with self._lock:
            current_size = min(self.size, self.capacity)
            return [self.data[i] for i in range(current_size)]

# --- Hypothesis Strategies ---
ir_strategy = st.builds(
    IR,
    ctx_id=st.integers(min_value=1, max_value=100),
    pos=st.integers(min_value=0, max_value=10000),
    phase=st.sampled_from([Phase.PREFILL, Phase.GENERATION, Phase.FINALIZE]),
    token=st.integers(min_value=0, max_value=32000),
    score=st.floats(min_value=-100.0, max_value=0.0)
)

@given(capacity=st.integers(min_value=1, max_value=50), irs=st.lists(ir_strategy, min_size=1, max_size=100))
def test_inv_bounded(capacity, irs):
    """INV-BOUNDED: バッファサイズは常にキャパシティ以下、超過時は overflow_count が記録される"""
    buf = IRBuffer(capacity)
    for item in irs:
        buf.push(item)
    
    if buf.size <= capacity:
        assert len(buf.snapshot()) == buf.size
        assert buf.overflow_count == 0
    else:
        assert len(buf.snapshot()) == capacity
        assert buf.overflow_count == (buf.size - capacity)

@given(ir=ir_strategy)
def test_inv_immutable(ir):
    """INV-IMMUTABLE: 生成後のIRフィールド変更は禁止される"""
    with pytest.raises(AttributeError):
        ir.pos = 9999