# Primary sources and implementation boundary

Accessed 2026-10-12. Vendor documents are reference inputs, not execution instructions or evidence that this project meets their standards.

| Source | Revision / section | Used for |
|---|---|---|
| https://verilator.org/guide/latest/install.html | Installation; project pins 5.040 | Source-build toolchain |
| https://docs.cocotb.org/en/v2.0.0/simulator_support.html | Verilator support | cocotb 2.0.0 / Verilator >=5.036 |
| https://docs.amd.com/r/en-US/ug586_7Series_MIS/Memory-Initialization-and-Calibration-Sequence | UG586 4.2, calibration | Boundary between transactional model and real DDR PHY |
| https://www.intel.com/content/www/us/en/docs/programmable/683660/15-1/transaction-layer.html | §8.2 Transaction Layer | PCIe layering; custom envelope is NOT this wire format |
| https://datasheets.raspberrypi.com/pcie/pcie-connector-standard.pdf | v1.1 2024-01-15, printed pp.3,5–7 | FFC pinout, 1 A power, control levels, cable <=50 mm and 90-ohm differential requirement |
| https://pip.raspberrypi.com/documents/RP-008218-DS | Raspberry Pi M.2 HAT+ schematic Rev 3, 2024-01-05, sheet 1 | M-key pin assignments, polarity inversion note, wake/reset/power reference |
| https://www.te.com/en/product-1-1734839-6.html | FFC 16-pin top-contact family | Connector mechanical reference; superseded part requires replacement qualification |
| https://www.te.com/en/product-1-2199230-4.html | M-key, 4.2 mm, 0.5 mm | M.2 connector mechanical reference; do not confuse with E-key 2199230-4 |
| https://jlcpcb.com/impedance | 4 layer 1.6 mm, JLC04161H-3313 | 0.0994 mm outer dielectric, Er 4.1; inner 1.265 mm core, Er 4.6; Cu 35/15.2/15.2/35 um |
| https://www.ti.com/lit/ds/symlink/tps62130.pdf | SLVSAG7F, §8–9 | Feedback, current/voltage limits, component selection and sequencing |
| https://www.ti.com/product/TPS62130#design-development | SLVM936A / SLVM436C | Original manufacturer SPICE models |
| https://docs.amd.com/v/u/en-US/ds181_Artix_7_Data_Sheet | DS181 v1.27.1, Table 2 and power sequence | Hypothetical Artix-7 rail voltages; currents are our assumptions |

No licensed PCI-SIG/JEDEC conformance testing or external field solver was performed. Locally downloaded reference PDFs and TI models preserve source attribution; excluded from future public packaging unless redistribution rights are reviewed.

## Additional executed design references
- TE 1-2199230-4 official M-key product and application specification 114-115006 Rev C: https://www.te.com/en/product-1-2199230-4.html
- TE manufacturer drawing G-2199230 Rev B3, sheet 3, hosted by SparkFun: https://cdn.sparkfun.com/assets/9/c/e/b/6/MicroMod_M.2_Connector_Datasheet_TE_2199230-4.pdf (visually inspected; identifies common family pad pattern and key-dependent omissions; latest part-specific review still required).
- Onsemi NC7SB3157 datasheet: https://www.onsemi.com/pdf/datasheet/nc7sb3157-d.pdf
- Diodes DMG1012T datasheet: https://www.diodes.com/datasheet/download/DMG1012T.pdf
- KiCad native CLI: https://docs.kicad.org/9.0/en/cli/cli.html
- KiCad official Ubuntu packaging: https://www.kicad.org/download/details/ubuntu/

Routing tool: [Freerouting 2.5.0 official release](https://github.com/freerouting/freerouting/releases/tag/v2.5.0), SHA-256 recorded in `hardware/reference_pcie_adapter/routing/README.md`. [Official CLI documentation](https://github.com/freerouting/freerouting/blob/master/docs/command_line_arguments.md) used for headless execution and disabled analytics/API. Board data remained in a network-disabled local container.
