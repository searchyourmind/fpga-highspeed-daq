# Engineering decisions

1. Preserve the supplied FIFO interface and full-reject policy. Add explicit pointer wrapping so depth 1 and non-powers-of-two are legal. A conservative full cycle costs a bubble but avoids an input-ready dependency on downstream ready.
2. Replace starter asynchronous reset with a consistent synchronous reset throughout; the original starter remains untouched in `provenance/Week1_Starter.zip`.
3. Carry sequence/frame metadata through all datapath stages. This makes reorder, loss, duplication and frame-marker faults observable independently of payload coincidences.
4. Saturation rather than wrapping gain: unsigned multiplication cannot silently turn a large sample into a small one. The golden model uses Python integer arithmetic.
5. Store-and-forward ring DMA with one owner. Avoid claiming continuous high-speed throughput while preserving bounded storage, descriptor validation and deterministic error semantics.
6. Separate memory commands/responses and packet queue capacity from RTL. Backpressure and response latency are independently controlled in verification.
7. Never use a protocol name as a conformance claim. Names `ddr_behavioral` and `pcie_transaction` describe inspiration and abstraction scope.
8. Keep original manufacturer analog models unchanged; record compatibility/convergence failures rather than replacing them with a fabricated waveform.
9. Use a container image for free toolchain dependencies. No system-level macOS install; record image digest and complete package versions.
10. PCB source, rendered outputs, connectivity tests, ERC and DRC are distinct evidence. Passing one does not prove the others or signal integrity.
