#!/bin/sh
set -eu
Xvfb :99 -screen 0 1600x900x24 -nolisten tcp >/tmp/daq-xvfb.log 2>&1 &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true' EXIT
sleep 1
export DISPLAY=:99
python3 hardware/reference_pcie_adapter/fill.py
python3 hardware/reference_pcie_adapter/check.py
python3 hardware/reference_pcie_adapter/check_routing.py
