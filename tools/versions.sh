#!/bin/bash
set -e
python --version
verilator --version
cocotb-config --version
yosys -V
ngspice --version
kicad-cli version
git --version
make --version | head -1
python -m pip freeze
cat /opt/verilator-source.sha256
