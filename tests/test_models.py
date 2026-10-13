from dataclasses import replace
import random
import pytest
from sim.ddr_behavioral.memory import Memory
from sim.pcie_transaction.transport import Link, Packet, ProtocolError
from sim.host_model.receiver import Host

@pytest.mark.parametrize('latency',[1,3,19])
def test_memory_burst_latency_and_stalled_response(latency):
    m=Memory(capacity=128,latency=latency,refresh_period=0,refresh_cycles=0)
    m.accept(0,True,64,range(8),length=8)
    assert m.response(latency-1) is None
    saved=m.response(latency)
    assert saved == m.response(latency+100) and not saved.error
    assert not m.ready(latency+100)
    m.consume(latency+100)
    m.accept(latency+101,False,64,length=8)
    assert m.consume(2*latency+101).data == tuple(range(8))

@pytest.mark.parametrize('address,length,data',[(-8,1,(1,)),(1,1,(1,)),(120,2,(1,2)),(0,0,()),(0,9,tuple(range(9))),(0,2,(1,)),(0,1,(-1,))])
def test_memory_bad_request_is_atomic(address,length,data):
    m=Memory(capacity=128,refresh_period=0,refresh_cycles=0)
    before=m.words.copy()
    m.accept(0,True,address,data,length)
    assert m.consume(3).error and m.words==before

def test_refresh_reset_and_order():
    m=Memory(capacity=128,queue_depth=2,refresh_period=10,refresh_cycles=3)
    assert [m.ready(t) for t in range(4)] == [False,False,False,True]
    m.accept(3,True,0,(99,)); m.accept(4,False,0)
    assert m.consume(10).data==()
    assert m.consume(11).data==(99,)
    m.accept(13,True,8,(77,)); m.reset()
    assert m.response(100) is None and m.words[1]==77

def test_random_bursts():
    rng=random.Random(7301); m=Memory(capacity=1024,refresh_period=0,refresh_cycles=0)
    reference=[0]*128
    for t in range(300):
        length=rng.randint(1,8); start=rng.randint(0,128-length)
        data=tuple(rng.getrandbits(64) for _ in range(length))
        m.accept(t*8,True,start*8,data,length); m.consume(t*8+3)
        reference[start:start+length]=data
        m.accept(t*8+4,False,start*8,length=length)
        assert m.consume(t*8+7).data==tuple(reference[start:start+length])

def test_link_latency_capacity_and_host():
    link=Link(latency=5,capacity=1); host=Host(7,0x1000,3)
    for n in range(3):
        link.accept(n,data=n,address=0x1000,tag=7,length=24,sop=n==0,eop=n==2,last=n==2)
    assert not link.ready() and link.deliver(6) is None
    assert link.deliver(7,False) is None
    host.receive(link.deliver(7))
    assert host.records==[0,1,2] and host.done and link.ready()

@pytest.mark.parametrize('fault',['crc','tag','address','length','last','duplicate'])
def test_host_rejects_faults(fault):
    p=Packet(4096,2,8,(17,),True).seal(); h=Host(2,4096,1)
    if fault=='crc': p=replace(p,payload=(18,))
    if fault=='tag': p=replace(p,tag=3).seal()
    if fault=='address': p=replace(p,address=4104).seal()
    if fault=='length': p=replace(p,length=16).seal()
    if fault=='last': p=replace(p,last=False).seal()
    if fault=='duplicate': h.receive(p)
    with pytest.raises(ProtocolError): h.receive(p)

def test_link_corruption_and_reset():
    l=Link(); l.corrupt_next=True
    l.accept(0,data=7,address=0,tag=1,length=8,sop=True,eop=True,last=True)
    with pytest.raises(ProtocolError): l.deliver(7).validate()
    l.accept(8,data=1,address=0,tag=1,length=16,sop=True,eop=False,last=False)
    l.reset(); assert l.partial==[] and not l.pending

@pytest.mark.parametrize('kwargs',[
    dict(sop=False,eop=True,last=True,length=8),
    dict(sop=True,eop=False,last=True,length=8),
    dict(sop=True,eop=True,last=True,length=16),
])
def test_malformed_packet(kwargs):
    with pytest.raises(ProtocolError):
        Link().accept(0,data=0,address=0,tag=0,**kwargs)

@pytest.mark.parametrize('kwargs',[
    {'address':-8},{'address':2**64},{'tag':-1},{'tag':65536},
    {'length':-8},{'length':65536},{'payload':(-1,)},{'payload':(2**64,)},{'last':2},
])
def test_packet_encoding_ranges(kwargs):
    p=replace(Packet(0,0,8,(1,),True),**kwargs)
    with pytest.raises(ProtocolError):p.seal()

def test_packet_page_and_last_address():
    with pytest.raises(ProtocolError):Packet(0xff8,3,16,(1,2),True).seal().validate()
    Packet(2**64-8,3,8,(1,),True).seal().validate()

def test_host_router_keeps_delayed_contexts_and_tag_ownership():
    from sim.host_model.receiver import HostRouter
    r=HostRouter(max_active=2)
    a=r.register(7,0x1000,1);b=r.register(8,0x2000,1)
    with pytest.raises(ProtocolError):r.register(7,0x3000,1)
    with pytest.raises(ProtocolError):r.register(9,0x3000,1)
    with pytest.raises(ProtocolError):r.take(7)
    r.receive(Packet(0x1000,7,8,(11,),True).seal())
    assert a.done and not b.done
    assert r.take(7)==[11]
    r.receive(Packet(0x2000,8,8,(22,),True).seal());assert r.take(8)==[22]
    r.register(7,0x3000,1);r.reset();assert not r.contexts
    with pytest.raises(ProtocolError):r.receive(Packet(0x3000,7,8,(33,),True).seal())
