"""Finite ordered transaction memory; not a DDR controller/PHY or timing model."""
from collections import deque
from dataclasses import dataclass

@dataclass(frozen=True)
class Response:
    data: tuple[int, ...]
    error: bool
    due: int

class Memory:
    def __init__(self, capacity=4096, latency=3, max_burst=8, queue_depth=1,
                 refresh_period=37, refresh_cycles=5):
        if capacity <= 0 or capacity % 8 or latency < 1 or max_burst < 1 or queue_depth < 1:
            raise ValueError("Invalid memory configuration")
        if refresh_period < 0 or not 0 <= refresh_cycles <= refresh_period:
            raise ValueError("Invalid refresh configuration")
        self.capacity, self.latency = capacity, latency
        self.max_burst, self.queue_depth = max_burst, queue_depth
        self.refresh_period, self.refresh_cycles = refresh_period, refresh_cycles
        self.words = [0] * (capacity // 8)
        self.pending = deque()
        self.requests = []

    def ready(self, cycle):
        refreshing = self.refresh_period and cycle % self.refresh_period < self.refresh_cycles
        return not refreshing and len(self.pending) < self.queue_depth

    def accept(self, cycle, write, address, data=(), length=1, inject_error=False):
        if not self.ready(cycle):
            raise RuntimeError("Command accepted without ready")
        data = tuple(data)
        error = (inject_error or address < 0 or address % 8 != 0 or length < 1
                 or length > self.max_burst or address + length * 8 > self.capacity
                 or (write and len(data) != length)
                 or any(not 0 <= v < 2**64 for v in data))
        result = ()
        if not error:
            index = address // 8
            if write:
                self.words[index:index+length] = data
            else:
                result = tuple(self.words[index:index+length])
        self.pending.append(Response(result, bool(error), cycle+self.latency))
        self.requests.append((cycle, bool(write), address, length, bool(error)))

    def response(self, cycle):
        return self.pending[0] if self.pending and self.pending[0].due <= cycle else None

    def consume(self, cycle):
        if self.response(cycle) is None:
            raise RuntimeError("No response available")
        return self.pending.popleft()

    def reset(self):
        """Abort pending acknowledgments; accepted writes remain in memory."""
        self.pending.clear()
