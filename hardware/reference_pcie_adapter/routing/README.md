# Routing provenance and reproduction

`tracks.json` is the authoritative, checked 400-item native routing snapshot (integer nanometers). `apply_routing.py` replays it over the generated board. The ordinary `make pcb` command does not replace routing; `make pcb-rebuild` explicitly does.

`pair-baseline.json` is the original manually constructed differential geometry. `check_routing.py` compares every pair in both directions, by layer, via count/position and width, with 1um tolerance; it also prohibits inner-layer signal tracks. Actual observed deviations are floating-point roundoff only. Length reports exclude electrical via/connector delay.

A preserved first-stage DSN/SES records Freerouting 2.5.0 routing on the outer layers, followed by local manual completion and repeated native KiCad DRC. `local_completion.py` and `logic_supply_completion.py` record those additions; they are historical one-shot scripts and must not be applied repeatedly to the final board. Use the complete snapshot for deterministic reproduction.

Freerouting official release: https://github.com/freerouting/freerouting/releases/tag/v2.5.0
JAR SHA-256: f6f51bb02245e8e717f9359bd260cc9c5c0b1bc0acc8b7cb2cd5b8ffeb5de3c7
Tool source/license: https://github.com/freerouting/freerouting (GPL-3.0); JAR is not redistributed here.

Actual router invocation used Java 25 in `fpga-daq-router:1`, with `--network none`, `-da`, `--gui.enabled=false`, `--api_server.enabled=false`, `--router.layers.routable=true,false,false,true`, 20 passes and 3GB heap. Router warnings about fixed geometry are retained; native KiCad checks are authoritative for this project and were not suppressed. Passing those checks still does not establish SI, thermal suitability or manufacturing readiness.
