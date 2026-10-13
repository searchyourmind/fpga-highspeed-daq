# Assumptions and limitations

| Area | Decision / risk | Status boundary |
|---|---|---|
| Source | Synthetic source can pause indefinitely | No real ADC overflow/clock relationship modeled |
| Reset | Active-low synchronous reset, all stages/environment coordinated | No asynchronous reset deassertion/CDC analysis |
| Capacity | One descriptor <=32 records by default | No concurrent descriptor ring or sustained write/read overlap |
| Memory | One outstanding 64-bit command; bursts only at model API | Not AXI, MIG, DDR controller or PHY |
| Transport | Ordered bounded modeled link; custom CRC32 | No PCIe protocol compliance or retry; corruption detected at host |
| Error handling | Memory error returns status 5; software must discard/abort partial host transfer | No data rollback of already accepted writes |
| Completion | Final packet beat accepted by link input | Host delivery can occur later |
| Performance | Count actual simulated cycles including control overhead | No MHz/Fmax/GB/s conversion without physical implementation |
| Synthesis | Technology-independent cells | No FPGA target, IO constraints, place/route or static timing closure |
| Power | Assumed loads and component calculations | No device power estimator or EMI/physical measurements; separate board thermal screen is unqualified |
| Adapter | Separate Pi5-M.2 design-only exercise | No manufacture, assembly, channel/physical SI validation, interoperability or compliance |
| Cadence | Neither installed nor licensed | Cadence hands-on NOT COMPLETED |

A reset discards active descriptors and pending packets/acknowledgments. Accepted writes remain in memory; a new job overwrites its own ring positions. Sequence restarts at zero for each job. Frame size zero is explicitly normalized to one; gain and frame size are captured at descriptor acceptance. A malformed descriptor emits an error completion and no memory operations.
