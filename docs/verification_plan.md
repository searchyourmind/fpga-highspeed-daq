# Verification plan and coverage map

| Requirement | Executable evidence |
|---|---|
| Counter toolchain smoke | starter `tb/test_counter.py` |
| FIFO order/full/reset/random stall | unchanged starter `tb/test_stream_fifo.py` |
| Depth 1,3,8,16/wrap/100-cycle full stall | `tb/test_fifo_extended.py` |
| Gain zero/unity/saturation, odd/zero frame length, long stalls | `tb/test_streaming.py` |
| Memory burst latency, response backpressure, bounds and atomic rejection | `tests/test_models.py` |
| Abstract refresh, queue ordering, retained writes after reset | `tests/test_models.py` |
| Packet latency, capacity, malformed SOP/EOP and header | `tests/test_models.py` |
| Host CRC/tag/address/length/final/duplicate rejection | `tests/test_models.py` |
| Complete path / ring wrap / source vs host | `tb/test_end_to_end.py`, 15 fixed-seed configurations |
| Invalid descriptor no memory traffic | `invalid_descriptors_and_recovery` |
| Completion stability / ordering and 500-cycle stalls | `long_backpressure_and_descriptor_order` |
| Write/read error recovery | `memory_faults_abort_and_next_job` |
| Reset at multiple active stages | `reset_inflight_at_multiple_stages` |
| RTL payload corrupted after packetization | `transport_corruption_is_detected` |
| Configuration capture at acceptance | changed gain/frame input immediately after descriptor handshake |
| 4 KiB boundary and final64-bit address | `tb/test_e2e_extended.py`, both RTL configurations |
| Delayed delivery across4 host contexts | `next_descriptor_before_previous_host_delivery` |
| Repeated jobs, odd257-record ring, depth3 FIFO | `large_ring_stress_and_repeated_jobs`,18 additional MATCH scenarios |
| Invalid packet encoding bounds | `tests/test_models.py` |
| Missing/failed/skipped evidence rejected | `tests/test_runner_evidence.py`, actual `tools/test_failure_gate.py` probe |
| Generic loop/clock/topological timing audit | `tools/timing_audit.py`; no device STA |
| No latches, unresolved cells or hierarchy errors | `make lint`, `make synthesis` |

Pass/fail counts are read from actual JUnit XML and logs, not this planned matrix. Functional coverage is requirement-based; no line/toggle coverage percentage or formal proof is claimed. Simulation assertions check valid/payload stability, completion stability, and FIFO occupancy. Random seeds are fixed and reported in the CSV. Burst support belongs to the memory model; current RTL memory transactions have one record each.
