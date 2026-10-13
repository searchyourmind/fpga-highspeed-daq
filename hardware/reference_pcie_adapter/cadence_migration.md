# Cadence migration - NOT COMPLETED hands-on
No licensed OrCAD X / Allegro session was used. KiCad work must not be represented as Cadence experience.

When licensed access becomes available:
1. In OrCAD/System Capture, recreate the power-down isolation subsection using the reviewed pin map and actual part symbols. Audit TPS62130A PG shutdown behavior, NC7SB3157 pins 1/3/4/6 and DMG1012T gate/source/drain.
2. Export/compare a netlist against `outputs/reference.net`. Import/export netlist compatibility is not guaranteed; verify each pin and footprint rather than assuming file-format parity.
3. In Allegro Constraint Manager, define CLK, RX, TX differential pairs, 90-ohm target, geometry from the approved stack, and matched-delay/via rules. The current KiCad dimensions are preliminary.
4. Recreate a small connector breakout, adjacent return vias and a continuous plane. Run actual electrical/physical DRC and record reports plus the licensed product/version.
5. Complete the open layout and component-selection gates before producing DRAFT fabrication files. No ordering or manufacturing is authorized.
