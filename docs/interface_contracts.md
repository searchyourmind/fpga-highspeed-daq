# Interface contracts (baseline, before implementation)

## Clock/reset
All synthesizable modules use one clock and active-low **synchronous** reset. Reset takes effect on the next rising edge, flushes in-flight valid state and descriptor ownership, and emits no completion for an aborted transfer. Memory contents are retained, but the simulation environment drops pending responses when reset is sampled. Drivers discard pre-reset scoreboards. No CDC is claimed.

## Sample and stream
Transfer occurs only on a rising edge with valid and ready asserted. A producer must preserve valid and all payload/metadata while stalled. The synthetic source latches frame size and total length on start; no source overflow is modeled because it is backpressure-capable.
Sample n = (73*n + 19) modulo 65536. Unsigned processing: min(sample*gain,65535), gain an unsigned 8-bit integer; no rounding. Frame length is positive; last is asserted on each frame boundary and on the final partial frame.
The canonical 64-bit memory record is {frame_id[14:0], last, sequence[31:0], sample[15:0]}. Sequence resets per descriptor. A stream transports 16-bit samples plus these sidebands; one record occupies eight memory bytes.

## FIFO
Parameter DATA_W>0, DEPTH>=1, including non-power-of-two depths. Register storage, combinational read, no empty fall-through. Preserve starter's policy: full rejects a push even if a pop is accepted that cycle. Occupancy always 0..DEPTH; simultaneous accepted push/pop preserves occupancy. Reset clears pointers/count, not storage.

## Memory transaction abstraction
64-bit aligned byte addresses, one outstanding command at a time in RTL. Command = write/address/data; response = data/error. Request and response each have independent ready/valid. Python behavioral memory also exposes bounded burst requests for unit tests. Ordered responses, configurable latency and periodic abstract refresh stalls; finite capacity, bounds and alignment errors. Memory model is not synthesizable and is not a DDR3 controller, PHY, JEDEC timing model, or bank scheduler.

## Descriptors, ring and ownership
Descriptor = id, ring byte base, start index, record count, host byte address, owner. One accepted descriptor at a time. Validate owner=1, positive count <= ring capacity, start < capacity, 8-byte alignment, complete ring within model memory, and no host-address overflow. Index wraps at ring capacity. Controller owns accepted valid jobs until completion is consumed; software regains ownership on completion. Invalid descriptors complete with a nonzero status and generate no memory traffic. Status codes: 0 success, 1 memory range/alignment, 2 length/start, 3 host range/alignment, 4 ownership, 5 memory bus error. Completion must remain stable under backpressure. Reset aborts without completion.
Writing the complete finite descriptor precedes reading it; completion occurs after the final record is accepted by the modeled link input, not after host delivery. One descriptor in flight prevents overwriting unread ring data. This is a bounded store-and-forward engine, not continuous acquisition or concurrent DMA.

## PCIe-like output
RTL packetizer emits 64-bit beats with SOP/EOP, packet base host address, tag, packet byte length, and descriptor-last. Max payload is parameterized in records (baseline 4 = 32 bytes). Partial final packets are supported. Packets end before crossing a 4 KiB address boundary, and the last addressed byte must fit64 bits; an8-byte record at2^64-8 is valid. MAX_WORDS is1..512. Python transport assembles packets, adds a custom CRC32 for fault injection, delays delivery and applies bounded queue backpressure. Host checks address/length/tag/CRC and reconstructs records. HostRouter keeps a bounded set of registered tag contexts (default16); tags cannot be reused until completed data is consumed. Reset aborts these contexts. RTL still accepts only one active descriptor at a time. This envelope is deliberately NOT wire-format PCIe TLP or LCRC. No BAR, enumeration, LTSSM, SerDes, DLLP, credit/replay protocol, or PCIe compliance.
