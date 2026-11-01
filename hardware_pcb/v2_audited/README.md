# Sanjeevni Nano Rover v2 - EasyEDA build pack

Everything here is generated from **`design.py`** (one source of truth). If you change a pin or part, edit `design.py`, run `python3 design.py`, and `netlist.csv`, `bom.csv`, `firmware/pinmap.h` and `docs/schematic.svg` all update together. The script also *checks* the design (duplicate GPIOs, PSRAM pins, USB pins, dangling nets, VINT wiring ...) and refuses to write files if a check fails.

| File | Use |
|---|---|
| `docs/schematic.svg` | One-page connection map - open it next to EasyEDA |
| `netlist.csv` | Every connection: net, part, pin |
| `bom.csv` | Parts. Search the **MPN** in EasyEDA; the LCSC # is a shortcut (confirm it) |
| `firmware/sanjeevni_nano.ino` + `pinmap.h` | Matching firmware |
| `docs/AUDIT.md` | What was wrong in v1 and what changed |

## Honest status
* Your v1 KiCad files cannot be imported usefully (empty schematic). I did **not** generate an EasyEDA/KiCad file I could not test; instead you build the schematic in EasyEDA from this netlist (about 1-2 hours) - this is reliable and also gives you correct footprints.
* Checked here: pin/net consistency (automated), firmware **syntax and types** against Arduino stubs (not a real board compile).
* **Not** verified here (no access to LCSC/datasheets from my sandbox): LCSC numbers except the ESP32 module, and your camera module's FPC pin order. Treat these as the first things to confirm.

## A. Before you draw anything
1. Buy / pick the **OV2640 24-pin FPC camera module** and download *its* datasheet. In `schematic.svg` block **J2**, each camera signal is listed by name; write down the module's pin number for each. Confirm the module is 3.3 V-only (on-board 2.8 V / 1.2 V regulators). If it exposes AVDD/DVDD pins, add a 2.8 V LDO (e.g. ME6211C28) for AVDD.
2. Buy a **protected** 3.7 V LiPo (built-in protection board), ~400 mAh. Check the JST wire order: red must go to J3 pin 1 (BAT+).
3. Buy N20 motors rated **3 V** (or 6 V if you accept slower speed). 6 V motors run at about 60 % speed on 3.7 V.

## B. Build the schematic in EasyEDA (Std or Pro, online)
1. New project -> New schematic.
2. For each block in `docs/schematic.svg` (U1, U2, U3, U4, U5, J1...): `Place -> Component` (Std: *LCSC parts*; Pro: *Library -> Search*), search the **MPN** (or the C-number) and place it. The footprint comes with the part.
3. Put a **net label** on every pin using the net name shown (same name = connected). `NC` pins get a "no connect" flag. Pins named the same on a part (GND, VBUS, D+ ...) all go to the same net.
4. Add the passives from the table at the bottom of the SVG / `bom.csv` (R1-R18, C1-C14, D1-D5).
5. Run **Design -> Check DRC (Schematic)**. Then compare with `netlist.csv`: in EasyEDA export the netlist and diff, or spot-check the power nets (`GND`, `+3V3`, `VBAT`, `VBAT_SW`, `VBUS`) first.

## C. PCB (Design -> Convert schematic to PCB)
* Outline **46 x 48 mm**, 2 layers, 1.6 mm, 3 mm corner radius, 4 x M2 holes at the corners (GND pads).
* Placement: camera FPC + IR LEDs at the **front edge**; **ESP32 module with its antenna end overhanging the edge** (or at least a 15 mm copper-free keep-out: no copper, tracks, battery or metal under/near the antenna); USB-C + slide switch + battery connector at the **rear**; motor pads on the **left/right edges**; DRV8833 near the motor pads; C3/C4/C5 right next to DRV8833 VM; C7/C6 right next to VINT/VCP; AP2112K close to the ESP32 3V3 pin with C8/C9 on its output.
* Tracks: `VBAT`, `VBAT_SW`, motor outputs, `+3V3` >= **0.5 mm**; signals 0.2-0.25 mm; keep `CAM_PCLK/XCLK` short and don't run them parallel to `USB_DP/DN`.
* Ground: fill both layers with GND, stitch with vias, and put **>= 4 vias under the DRV8833 and TP4056 exposed pads** (heat).
* Auto-router: use it only for the low-speed nets (LEDs, I2C, pull-ups). **Hand-route** the camera bus, USB pair and power.
* Run DRC. Then `Fabrication -> PCB Fabrication File (Gerber)` and the BOM/pick-and-place files for JLCPCB SMT.

## D. First power-up checklist (do in this order)
1. No ESP32 fitted yet (or sockets): apply 5 V on USB-C with a current-limited supply -> `VBUS` = 5 V, charge LED on **only** with a cell connected.
2. Slide switch on: `+3V3` must read **3.25-3.35 V** with the cell at 3.7 V (this is what the AMS1117 failed to do).
3. Check `VM` = battery voltage and that `VINT` is **not** at battery voltage (it is the DRV8833's own internal rail).
4. Fit ESP32, hold BOOT, tap EN, flash `sanjeevni_nano.ino` over USB (Arduino IDE: ESP32S3 Dev Module, OPI PSRAM, USB CDC On Boot = Enabled).
5. Join Wi-Fi `SANJEEVNI-NANO-01` (change the password in the sketch first), open `http://192.168.4.1/telemetry`, then `http://192.168.4.1:81/stream.mjpg`.
6. Test motors with wheels lifted: `/drive?cmd=w&spd=120`.

## Known limits
* Total rover width = board + motors + wheels; with 48 mm board and N20 motors mounted inside, wheels add ~12 mm. The 5 cm envelope applies to the board, not to the finished rover - decide the wheel layout before finalising the outline.
* 400 mAh gives roughly 30-60 min of streaming (estimate, not measured).
* The ESP32's own 2.4 GHz Wi-Fi will not go far through reinforced concrete - plan a tether or relay for real rubble.
