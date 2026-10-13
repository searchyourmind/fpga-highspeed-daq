"""Strict finite-descriptor host sink for the custom PCIe-like transport."""
from sim.pcie_transaction.transport import ProtocolError

class Host:
    def __init__(self, tag, address, count, max_words=4):
        self.tag, self.address, self.count, self.max_words = tag,address,count,max_words
        self.records = []
        self.done = False

    def receive(self, packet):
        packet.validate(self.max_words)
        if self.done or packet.tag != self.tag or packet.address != self.address+len(self.records)*8:
            raise ProtocolError('Unexpected tag, address, duplicate, or completion order')
        new_count = len(self.records)+len(packet.payload)
        if new_count > self.count or packet.last != (new_count == self.count):
            raise ProtocolError('Invalid final packet or descriptor length')
        self.records.extend(packet.payload)
        self.done = packet.last


class HostRouter:
    """Keep receive contexts alive after RTL completion and until host consumption.

    RTL completion means the final beat entered the bounded link, not that the
    delayed host received it. A tag cannot be recycled until its context is taken.
    """
    def __init__(self, max_active=16, max_words=4):
        if max_active < 1:
            raise ValueError('max_active must be positive')
        self.max_active, self.max_words = max_active, max_words
        self.contexts = {}

    def register(self, tag, address, count):
        if tag in self.contexts or len(self.contexts) >= self.max_active:
            raise ProtocolError('Tag still owned or host context capacity exhausted')
        if not 0 <= tag < 2**16 or count < 1 or address < 0 or address % 8 or address + count*8 > 2**64:
            raise ProtocolError('Invalid host descriptor')
        host = Host(tag, address, count, self.max_words)
        self.contexts[tag] = host
        return host

    def receive(self, packet):
        if packet.tag not in self.contexts:
            raise ProtocolError('No registered host context for tag')
        self.contexts[packet.tag].receive(packet)

    def take(self, tag):
        if tag not in self.contexts or not self.contexts[tag].done:
            raise ProtocolError('Host data not complete')
        return self.contexts.pop(tag).records

    def reset(self):
        self.contexts.clear()
