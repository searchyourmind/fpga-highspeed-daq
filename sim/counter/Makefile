SIM ?= verilator
TOPLEVEL_LANG = verilog
VERILOG_SOURCES = $(abspath ../../rtl/counter.sv)
COCOTB_TOPLEVEL = counter
COCOTB_TEST_MODULES = test_counter
export PYTHONPATH := $(abspath ../../tb):$(PYTHONPATH)
include $(shell cocotb-config --makefiles)/Makefile.sim
