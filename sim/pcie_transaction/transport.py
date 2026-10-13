"""Custom packet envelope. No PCIe wire encoding, credits, replay or PHY."""
from collections import deque
from dataclasses import dataclass, replace
import struct
import zlib

class ProtocolError(ValueError):
    pass

@dataclass(frozen=True)
class Packet:
    address: int
    tag: int
    length: int
    payload: tuple[int, ...]
    last: bool
    crc: int = 0

    def checksum(self):
        fields = ((self.address, 64), (self.tag, 16), (self.length, 16))
        if any(not isinstance(v, int) or not 0 <= v < 2**bits for v, bits in fields):
            raise ProtocolError('Packet header field outside encoded range')
        if self.last not in (False, True) or any(not isinstance(v, int) or not 0 <= v < 2**64 for v in self.payload):
            raise ProtocolError('Packet payload or final flag outside encoded range')
        header = struct.pack('<QHHB', self.address, self.tag, self.length, self.last)
        payload = b''.join(struct.pack('<Q', word) for word in self.payload)
        return zlib.crc32(header+payload)

    def seal(self):
        return replace(self, crc=self.checksum())

    def validate(self, max_words=4):
        checksum = self.checksum()
        if self.address % 8 or self.length != len(self.payload)*8 or not 0 < len(self.payload) <= max_words:
            raise ProtocolError('Invalid packet address/length')
        if (self.address & 4095) + self.length > 4096 or self.address + self.length > 2**64:
            raise ProtocolError('Packet crosses a 4 KiB page or address-space boundary')
        if self.crc != checksum:
            raise ProtocolError('Packet CRC mismatch (custom model CRC32)')

class Link:
    def __init__(self, latency=7, capacity=2, max_words=4):
        if latency < 1 or capacity < 1 or max_words < 1:
            raise ValueError('Invalid link configuration')
        self.latency, self.capacity, self.max_words = latency, capacity, max_words
        self.pending, self.partial = deque(), []
        self.header = None
        self.corrupt_next = False
        self.packet_count = 0

    def ready(self):
        return len(self.pending) < self.capacity

    def accept(self, cycle, *, data, address, tag, length, sop, eop, last):
        if not self.ready():
            raise ProtocolError('Transport queue overflow')
        header = (address, tag, length)
        if sop:
            if self.partial:
                raise ProtocolError('SOP inside packet')
            self.header = header
        elif not self.partial:
            raise ProtocolError('Missing SOP')
        if header != self.header:
            raise ProtocolError('Unstable packet metadata')
        if last and not eop:
            raise ProtocolError('Descriptor end without EOP')
        self.partial.append(data)
        if len(self.partial) > self.max_words:
            raise ProtocolError('Payload exceeds configured limit')
        if eop:
            packet = Packet(address,tag,length,tuple(self.partial),bool(last)).seal()
            packet.validate(self.max_words)
            if self.corrupt_next:
                packet = replace(packet, payload=(packet.payload[0]^1,)+packet.payload[1:])
                self.corrupt_next = False
            self.pending.append((cycle+self.latency,packet))
            self.partial, self.header = [], None
            self.packet_count += 1

    def deliver(self, cycle, ready=True):
        if ready and self.pending and self.pending[0][0] <= cycle:
            return self.pending.popleft()[1]
        return None

    def reset(self):
        self.pending.clear()
        self.partial, self.header = [], None
        self.corrupt_next = False
