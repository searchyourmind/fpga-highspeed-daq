# Generic synthesis

`make synthesis` runs Yosys over the actual RTL hierarchy with `SYNTHESIS` defined so simulator-only assertions are excluded. It runs `hierarchy -check`, generic `synth -noabc`, `check -assert`, JSON statistics and a latch audit of the emitted netlist.

Results live under `reports/`. A successful run demonstrates tool acceptance and generic logic elaboration/optimization, **not** a mapped FPGA build, cell-library timing, silicon area, LUT use or Fmax. No part is targeted and no timing slack is reported. Register-array FIFO implementation may infer different storage resources in a vendor flow.

The future hardware timing path includes launch flip-flop clock-to-Q, combinational logic, routing and destination setup time. Hold checks require minimum-delay analysis and actual clock skew. Clock constraints and timing exceptions need a concrete target, actual interfaces, and place-and-route. This baseline has one clock; it has no validated CDC design.

## Executed structural timing audit
`make timing` re-synthesizes the current RTL, flattens it, rejects combinational loops,
checks register clock connectivity and executes `ltp -noff`. Results are in
`reports/timing-audit.json` and `reports/longest-path.txt`. Path length is a number of
generic cells, not time. No setup/hold slack or Fmax is inferred from it.

`constraints/example.sdc` records an explicit, unapproved 100 MHz scenario and I/O
budgets without false-pathing the synchronous reset. It is not a substitute for a
selected FPGA part, a delay model or routed static timing analysis. Timing remains
PARTIAL until that flow exists.
