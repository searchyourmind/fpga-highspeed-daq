# DESIGN EXAMPLE ONLY. Not applied to a calibrated library or routed FPGA.
# Assumed external contract: 100 MHz, input/output budgets shown below.
# Replace these assumptions with a selected device and actual interfaces.
create_clock -name sys_clk -period 10.000 [get_ports clk]
set_clock_uncertainty 0.200 [get_clocks sys_clk]
set_input_delay -max 1.000 -clock sys_clk [remove_from_collection [all_inputs] [get_ports clk]]
set_input_delay -min 0.200 -clock sys_clk [remove_from_collection [all_inputs] [get_ports clk]]
set_output_delay -max 1.000 -clock sys_clk [all_outputs]
set_output_delay -min 0.200 -clock sys_clk [all_outputs]
# rst_n is synchronous: do not hide its path with a false-path exception.
