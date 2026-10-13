SIM ?= verilator
TOPLEVEL_LANG = verilog
VERILOG_SOURCES = $(abspath ../../rtl/stream_fifo.sv)
COCOTB_TOPLEVEL = stream_fifo
COCOTB_TEST_MODULES = test_stream_fifo
export PYTHONPATH := $(abspath ../../tb):$(PYTHONPATH)
include $(shell cocotb-config --makefiles)/Makefile.sim
