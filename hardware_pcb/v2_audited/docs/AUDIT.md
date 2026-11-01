# Audit of the uploaded `hardware_pcb/` (v1) - what was wrong

| # | Problem in v1 | Why it matters | Fixed in v2 |
|---|---|---|---|
| 1 | `sanjeevni_nano_rover.kicad_sch` is 2 KB: **1 wire + 1 label, zero components** | Importing it gives a blank page. README promised "Boom! Tumhara schematic open ho jayega" - it can't | Full connection map + netlist generated from one source (`design.py`) |
| 2 | `.kicad_pcb` contains only an outline, 4 mounting holes and silkscreen text; it also uses `;;` comments, which are not valid KiCad syntax | File would fail to parse; no footprints/pads/tracks exist | Build the PCB in EasyEDA from the netlist (steps in README) |
| 3 | README: "Auto-router will route everything perfectly in 15 s" | Not true; ESP32 antenna, USB, DRV8833 thermal pad and power tracks need manual care | Layout rules in README |
| 4 | **AMS1117-3.3** regulator on a 3.7 V LiPo | AMS1117 needs ~1.1 V headroom: at 3.7 V it outputs roughly 2.6 V, below ESP32 minimum -> constant brown-outs | AP2112K-3.3 (0.25 V dropout) |
| 5 | README wires **VINT to battery** (`VM, VINT`) | VINT is DRV8833's internal rail; it needs a 2.2 uF cap to GND. Tying it to VBAT can destroy the driver | VINT only to C7 (2.2 uF) - enforced by an automatic check |
| 6 | No **USB data lines** to the ESP32 | USB-C could charge but the board could not be programmed | D+/D- -> GPIO20/19 through USBLC6 ESD protection; UART debug header J8 as backup |
| 7 | TP4056 **PROG = 1.2 k = 1 A** into a 400 mAh cell | 2.5 C charging - overheats / shortens battery life, can be unsafe | 5.6 k = ~215 mA |
| 8 | SS14 Schottky in the battery path | A series diode drops 0.3-0.5 V of a 3.7 V supply (~10 % of your voltage and runtime), and it cannot protect the charger pin | Removed; use a keyed connector + protected LiPo and verify polarity (J3 note). A P-MOSFET ideal-diode can be added later if you want hard reverse protection |
| 9 | No I2C pull-ups | VL53L1X / MPU6050 breakouts differ; some have none | R9/R10 4.7 k (DNP if your breakouts include them) |
| 10 | nSLEEP described as pulled **up** in README but driven from GPIO8 in firmware | Motors could twitch during boot | 100 k pull-down: motors asleep until firmware wakes them |
| 11 | 5.08 mm **screw terminals** for N20 motors | Each terminal is bigger than the motor on a 46x48 mm board | Direct solder pads |
| 12 | BOM: ESP32-S3-WROOM-1-N8R8 listed as **C2913200** | LCSC page shows N8R8 = **C2913201** | Corrected. Every other LCSC number is marked "confirm" |
| 13 | Firmware streams video **inside the single-threaded port-80 server** | While a video client is connected, `/drive` cannot be answered -> rover uncontrollable (the dashboard calls `/drive` with a 0.35 s timeout) | Stream on port 81 in its own task |
| 14 | Firmware telemetry: `battery_pct` hard-coded 95, tilt and obstacle never read | Dashboard would show invented numbers; no flip/collision protection | Real ADC battery, MPU6050 tilt, VL53L1X distance, stop logic |
| 15 | Firmware uses `ledcSetup/ledcAttachPin` only | Does not compile on Arduino-ESP32 core 3.x | Works on 2.0.x and 3.x |
| 16 | No battery-voltage sense, no motor-fault read, camera PWDN/RESET unspecified | Cannot know battery state; camera may sleep/reset randomly | R15/R16 divider to GPIO9, nFAULT -> GPIO42, PWDN tied low, RESET pulled high |

## Project-folder hygiene (outside the PCB)
The zip also contains `server.key`, `server.crt`, `sanjeevni.db`, `server.log`, `__pycache__/` and a README with the path `/home/ece/.gemini/...`.
Do not publish or share the zip with `server.key` inside - regenerate the certificate and delete these files before sending it to anyone.
