"""External oracle checks: no RTL state, Packet checksum or golden implementation reuse."""
from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.path.insert(0,str(R/'tb'))
from reference_model import records
from sim.pcie_transaction.transport import Packet

def bitwise_crc(data):
 crc=0xffffffff
 for byte in data:
  crc^=byte
  for _ in range(8):crc=(crc>>1)^((0xedb88320) if crc&1 else 0)
 return crc^0xffffffff
assert bitwise_crc(b'123456789')==0xcbf43926
# Explicit byte vector built from the public envelope contract, no struct/Packet encoding call.
header=bytes.fromhex('00100000000000000700080001')
payload=bytes.fromhex('efcdab8967452301')
p=Packet(4096,7,8,(0x0123456789abcdef,),True)
assert p.checksum()==bitwise_crc(header+payload)
# Manually decoded three-record sequence/frame/last values, then separately packed literals.
known=[0x0000000000000039,0x0001000000010114,0x00030000000201ef]
assert records(3,2,3)==known
assert records(1,0,255)==[0x00010000000012ed]
r={'status':'PASS','checks':['CRC32 polynomial implementation verified against published standard check vector123456789=cbf43926','Custom envelope checksum matched independently serialized fixed bytes and bitwise CRC','Golden oracle matched manually packed3-record partial-frame vector and frame-zero/single-record vector'],'known_packet_crc32':hex(bitwise_crc(header+payload)),'scope':'Four supplemental audit checks, not added to the63 production tests. This validates the custom envelope, not PCIe LCRC. Mathematical oracle shares specification, but no DUT state or simulated memory is consulted.'}
O=R/'results/release-audit';O.mkdir(parents=True,exist_ok=True);(O/'independent-oracles.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
