# Evidence-backed resume bullets

Choose two or three relevant bullets. Project is AI-assisted; be ready to explain the authored/reviewed implementation and the recorded defects. Do not describe this as employment, measured hardware work or Cadence experience.

## FPGA / RTL applications

- Developed a single-clock SystemVerilog acquisition and DMA pipeline with ready/valid buffering, saturating gain, descriptor validation, ring-buffer writes and page-bounded packet readback; verified 33 end-to-end scenarios with independent record scoreboarding.
- Automated 63 passing pytest/cocotb tests in Verilator, covering stalls, reset/error recovery, ring wrap and address boundaries; independently challenged the checks with six isolated fault injections and reproduced the suite from a clean local Git checkout with a recorded Docker toolchain.
- Debugged 4 KiB packet-boundary crossings, final-address overflow rejection and completion-before-host-delivery handling; ran Yosys generic synthesis and structural checks with no inferred latches or combinational loops.

Use "DDR behavioral model" and "custom PCIe-like transaction model." Do not claim a DDR3 controller, PCIe endpoint, timing closure, FPGA implementation utilization, Fmax or measured bandwidth.

## Board / hardware design applications

- Built a separate four-layer Pi 5 FFC-to-M.2 reference carrier in KiCad and regenerated native ERC/DRC/connectivity checks with zero reported violations; maintained a conditional BOM, mechanical envelopes and explicit fabrication hold points.
- Modeled power distribution, regulator transients, thermal spreading and differential impedance; identified remaining voltage-budget deficits of 4.55/22.61 mV and corrected a copper-thickness inconsistency that exposed six failing thermal screening cases.
- Evaluated dielectric stack, trace width/spacing, copper profile and solder-mask sensitivity with a finite-volume electrostatic model; documented failed process corners and unqualified alternatives without claiming channel compliance or measured performance.

The board is design-only, separate from the DAQ RTL. Do not claim successful bring-up, certified SI/PI, thermal qualification, manufacturing release or installed hardware. Generic synthesis is not device timing closure. All quantities above are simulations/checks, not physical measurements.
