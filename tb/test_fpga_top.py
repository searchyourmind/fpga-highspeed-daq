"""Board top driven only through its UART pins, as the PC would drive it."""
import os, struct
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge
from reference_model import records

CPB=int(os.getenv('FPGA_CLKS_PER_BIT','16'))
MAX_WORDS=4

def descriptor(tag,start,length,base,host,owner,frame,gain):
    return bytes([0x5A])+struct.pack('<HHHIQBHB',tag,start,length,base,host,owner,frame,gain)

def expected_beats(tag,length,host,frame,gain):
    """Independent packetization: <=MAX_WORDS beats per packet, never across a 4 KiB page."""
    data=records(length,frame,gain); beats=[]; addr=host; left=length
    while left:
        size=min(left,MAX_WORDS,512-(addr&4095)//8)
        for i in range(size):
            beats.append(dict(data=data[len(beats)],addr=addr,tag=tag,length=size*8,
                              sop=int(i==0),eop=int(i==size-1),last=int(len(beats)==length-1)))
        addr+=size*8; left-=size
    return beats

def checksum(beats):
    c=0
    for b in beats:
        fold=(b['data']^b['data']>>32^b['addr']^b['addr']>>32^(b['tag']<<16|b['length'])
              ^(b['last']<<2|b['eop']<<1|b['sop']))&0xffffffff
        c=(((c<<1|c>>31)&0xffffffff)+fold)&0xffffffff
    return c

class Board:
    def __init__(self,d):
        self.d=d; self.rx=[]
        Clock(d.clk_25mhz,10,unit='ns').start()
        cocotb.start_soon(self.monitor())

    async def reset(self):
        d=self.d; d.ftdi_txd.value=1; d.btn_fire1.value=1
        await ClockCycles(d.clk_25mhz,5); d.btn_fire1.value=0
        await ClockCycles(d.clk_25mhz,25)
        assert int(d.ftdi_rxd.value)==1

    async def send(self,payload):
        for byte in payload:
            for bit in [0]+[byte>>i&1 for i in range(8)]+[1]:
                self.d.ftdi_txd.value=bit
                await ClockCycles(self.d.clk_25mhz,CPB)

    async def monitor(self):
        d=self.d
        while True:
            await FallingEdge(d.ftdi_rxd)
            await ClockCycles(d.clk_25mhz,CPB//2)
            assert int(d.ftdi_rxd.value)==0,'UART start bit glitch'
            byte=0
            for i in range(8):
                await ClockCycles(d.clk_25mhz,CPB); byte|=int(d.ftdi_rxd.value)<<i
            await ClockCycles(d.clk_25mhz,CPB)
            assert int(d.ftdi_rxd.value)==1,'UART framing error'
            self.rx.append(byte)

    async def run_job(self,*fields,preamble=b'',timeout=400_000):
        start=len(self.rx)
        await self.send(preamble+descriptor(*fields))
        for _ in range(timeout//CPB):
            await ClockCycles(self.d.clk_25mhz,CPB)
            beats,completions=parse(self.rx[start:])
            if completions: return beats,completions
        raise AssertionError('No completion received')

def parse(stream):
    beats=[]; completions=[]; i=0
    while i<len(stream):
        marker=stream[i]
        if marker&0xf8==0xd0 and i+9<=len(stream):
            beats.append(dict(sop=marker&1,eop=marker>>1&1,last=marker>>2&1,
                              data=int.from_bytes(bytes(stream[i+1:i+9]),'little'))); i+=9
        elif marker==0xc0 and i+10<=len(stream):
            tag,status,count,crc=struct.unpack('<HBHI',bytes(stream[i+1:i+10]))
            completions.append(dict(tag=tag,status=status,beats=count,checksum=crc)); i+=10
        elif marker&0xf8==0xd0 or marker==0xc0: break
        else: raise AssertionError(f'Unexpected report byte 0x{marker:02x} at {i}')
    return beats,completions

async def check_job(board,tag,start,length,base,host,frame,gain,preamble=b''):
    beats,completions=await board.run_job(tag,start,length,base,host,1,frame,gain,preamble=preamble)
    expected=expected_beats(tag,length,host,frame,gain)
    assert [b['data'] for b in beats]==[e['data'] for e in expected]
    assert [(b['sop'],b['eop'],b['last']) for b in beats]==[(e['sop'],e['eop'],e['last']) for e in expected]
    assert completions==[dict(tag=tag,status=0,beats=length,checksum=checksum(expected))]

@cocotb.test()
async def uart_descriptor_round_trip(d):
    board=Board(d); await board.reset()
    # Ring wrap from index 29, and a host address one word below a 4 KiB page.
    await check_job(board,0x1234,29,32,128,0x1ff8,13,2)
    # Invalid owner: rejected with status 4, no memory or link traffic.
    beats,completions=await board.run_job(0x55,0,4,0,0x1000,0,1,1)
    assert not beats and completions==[dict(tag=0x55,status=4,beats=0,checksum=0)]
    # Bytes before the 0x5A sync byte are ignored; gain 255 saturates.
    await check_job(board,7,0,5,0,0x1000,2,255,preamble=b'\x00\xff\x13')
    # Last 56 bytes of the 64-bit host space: exercises the upper address half.
    await check_job(board,0xbeef,10,7,512,2**64-56,3,9)
    assert int(d.led.value)>>3==4 and int(d.led.value)>>2&1==1

@cocotb.test()
async def reset_button_mid_job(d):
    board=Board(d); await board.reset()
    await board.send(descriptor(1,0,32,0,0x1000,1,4,3))
    await ClockCycles(d.clk_25mhz,40*CPB)
    await board.reset()
    await ClockCycles(d.clk_25mhz,20*CPB)
    board.rx.clear()
    await check_job(board,2,3,9,256,0x2000,4,6)
