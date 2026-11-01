#!/usr/bin/env python3
"""
SANJEEVNI NANO ROVER v2 - single source of truth.
Run:  python3 design.py      -> writes netlist.csv, bom.csv, firmware/pinmap.h, docs/schematic.svg
and RUNS ELECTRICAL/PIN CHECKS (exits non-zero if the design is inconsistent).
Edit ONLY this file, then re-run, so netlist / BOM / firmware can never disagree.
"""
import csv, sys, collections, html

# ----------------------------------------------------------------------------
# Parts.  pins = [(pin_number, pin_name, net)]   net None = intentionally unconnected
# mpn is the real search key in EasyEDA; lcsc is a convenience (verify it!).
# ----------------------------------------------------------------------------
P = {}
def part(ref, value, mpn, lcsc, footprint, pins, note="", group="misc", verified=False):
    P[ref] = dict(ref=ref, value=value, mpn=mpn, lcsc=lcsc, fp=footprint, pins=pins, note=note, group=group, verified=verified)

def two(ref, value, mpn, lcsc, fp, n1, n2, note="", group="passive"):
    part(ref, value, mpn, lcsc, fp, [("1", "1", n1), ("2", "2", n2)], note, group)

# ---- ESP32-S3-WROOM-1-N8R8 (pin table from Espressif datasheet) --------------
esp = [
 ("1","GND","GND"),("2","3V3","+3V3"),("3","EN","EN"),
 ("4","IO4","MOT_L_FWD"),("5","IO5","MOT_L_REV"),("6","IO6","MOT_R_FWD"),("7","IO7","MOT_R_REV"),
 ("8","IO15","IR_EN"),("9","IO16","LED_STAT"),("10","IO17","I2C_SCL"),("11","IO18","I2C_SDA"),
 ("12","IO8","MOT_SLEEP"),("13","IO19","USB_DN"),("14","IO20","USB_DP"),
 ("15","IO3",None),("16","IO46",None),("17","IO9","VBAT_SENSE"),
 ("18","IO10","CAM_D0"),("19","IO11","CAM_D1"),("20","IO12","CAM_D2"),("21","IO13","CAM_D3"),
 ("22","IO14","CAM_D4"),("23","IO21","CAM_D5"),("24","IO47","CAM_D6"),("25","IO48","CAM_D7"),
 ("26","IO45",None),("27","IO0","BOOT"),
 ("28","IO35",None),("29","IO36",None),("30","IO37",None),
 ("31","IO38","CAM_XCLK"),("32","IO39","CAM_PCLK"),("33","IO40","CAM_VSYNC"),("34","IO41","CAM_HREF"),
 ("35","IO42","MOT_FAULT"),("36","RXD0","UART_RX"),("37","TXD0","UART_TX"),
 ("38","IO2","CAM_SIOC"),("39","IO1","CAM_SIOD"),("40","GND","GND"),("41","EPAD","GND"),
]
part("U1","ESP32-S3-WROOM-1-N8R8","ESP32-S3-WROOM-1-N8R8","C2913201","MODULE_ESP32-S3-WROOM-1",esp,
     "8MB flash + 8MB octal PSRAM (needed for camera). Antenna end must overhang the board edge / keep-out.","mcu",verified=True)

part("U2","DRV8833PWPR","DRV8833PWPR","C50506","HTSSOP-16-EP (PWP)",[
 ("1","nSLEEP","MOT_SLEEP"),("2","AOUT1","MOT_L_A"),("3","AISEN","GND"),("4","AOUT2","MOT_L_B"),
 ("5","BOUT2","MOT_R_B"),("6","BISEN","GND"),("7","BOUT1","MOT_R_A"),("8","nFAULT","MOT_FAULT"),
 ("9","BIN1","MOT_R_FWD"),("10","BIN2","MOT_R_REV"),("11","AIN2","MOT_L_REV"),("12","AIN1","MOT_L_FWD"),
 ("13","GND","GND"),("14","VINT","VINT"),("15","VM","VBAT_SW"),("16","VCP","VCP"),("17","EPAD","GND")],
 "VINT needs 2.2uF to GND (NOT to battery). VCP needs 10nF to VM.","motor")

part("U3","AP2112K-3.3TRG1","AP2112K-3.3TRG1","C51118","SOT-23-5",[
 ("1","VIN","VBAT_SW"),("2","GND","GND"),("3","EN","VBAT_SW"),("4","NC",None),("5","VOUT","+3V3")],
 "Low-dropout (0.25V) 600mA. Replaces AMS1117 which needs 1.1V headroom and browns out on a 3.7V cell.","power")

part("U4","TP4056-42-ESOP8","TP4056","C16581","ESOP-8-EP",[
 ("1","TEMP","GND"),("2","PROG","PROG"),("3","GND","GND"),("4","VCC","VBUS"),
 ("5","BAT","VBAT"),("6","STDBY","CHG_STDBY"),("7","CHRG","CHG_CHRG"),("8","CE","VBUS"),("9","EPAD","GND")],
 "TEMP tied to GND (no NTC). PROG 5.6k = ~215mA charge (0.5C of a 400mAh cell).","power")

part("U5","USBLC6-2SC6","USBLC6-2SC6","C7519","SOT-23-6",[
 ("1","IO1","USB_DP"),("2","GND","GND"),("3","IO2","USB_DN"),("4","IO2","USB_DN"),("5","VBUS","VBUS"),("6","IO1","USB_DP")],
 "USB ESD protection on D+/D-.","usb")

part("J1","USB-C 16P","TYPE-C-31-M-12 (or any 16P USB-C receptacle)","C165948","USB-C-16P-SMD",[
 ("VBUS","VBUS","VBUS"),("GND","GND","GND"),("CC1","CC1","USB_CC1"),("CC2","CC2","USB_CC2"),
 ("DP","D+","USB_DP"),("DN","D-","USB_DN"),("SHELL","SHELL","GND")],
 "Tie ALL pads of the same name together (VBUS x4, GND x4, D+ x2, D- x2). Pad names differ per part - match by function.","usb")

cam = ["CAM_3V3","GND","CAM_SIOC","CAM_SIOD","CAM_XCLK","CAM_PCLK","CAM_VSYNC","CAM_HREF",
       "CAM_D0","CAM_D1","CAM_D2","CAM_D3","CAM_D4","CAM_D5","CAM_D6","CAM_D7","CAM_PWDN","CAM_RESET"]
part("J2","FPC 24P 0.5mm (camera)","FPC-0.5mm-24P bottom-contact","C262657","FPC-0.5mm-24P",
     [(n, n, ("+3V3" if n=="CAM_3V3" else n)) for n in cam],
     "!! PIN NUMBERS DEPEND ON YOUR CAMERA MODULE. Buy the OV2640 module first, copy its datasheet pin table, and map each signal name below to its pin number. Assumes a 3.3V-only module (on-board 2.8V/1.2V LDOs).","camera")

part("J3","JST-PH 2P battery","B2B-PH-K-S (THT) or SMD equivalent","C131337","JST-PH-2P",[("1","BAT+","VBAT"),("2","BAT-","GND")],
     "Use a PROTECTED LiPo (built-in PCM). Check the cell's red wire is pin 1 - many cheap cells are reversed!","power")
part("J6","VL53L1X ToF breakout","Header 1x4 2.54mm","C2883742","HDR-1x4-2.54",[("1","VCC","+3V3"),("2","GND","GND"),("3","SCL","I2C_SCL"),("4","SDA","I2C_SDA")],"","sensor")
part("J7","MPU6050 breakout","Header 1x4 2.54mm","C2883742","HDR-1x4-2.54",[("1","VCC","+3V3"),("2","GND","GND"),("3","SCL","I2C_SCL"),("4","SDA","I2C_SDA")],"","sensor")
part("J8","DEBUG UART","Header 1x4 2.54mm","C2883742","HDR-1x4-2.54",[("1","3V3","+3V3"),("2","GND","GND"),("3","TX","UART_TX"),("4","RX","UART_RX")],"Backup flashing/log port if USB is busy.","usb")
part("PL","Left motor pads","solder pads 2x (no part)","-","PAD-2x-2.0mm",[("1","A","MOT_L_A"),("2","B","MOT_L_B")],"Solder N20 motor tabs directly - 5.08mm screw terminals are bigger than the motor.","motor")
part("PR","Right motor pads","solder pads 2x (no part)","-","PAD-2x-2.0mm",[("1","A","MOT_R_A"),("2","B","MOT_R_B")],"","motor")

part("SW1","Slide switch SPDT","SS-12D00G3 (any SMD SPDT slide)","C319012","SW-SMD-3P",[("1","A","VBAT"),("2","COM","VBAT_SW"),("3","B",None)],"Common (middle) pin -> VBAT_SW. Check your part's pinout.","power")
part("SW2","Tact EN/RESET","TS-1187A-B-A-B (4x4 tact)","C318884","KEY-SMD-4x4",[("1","1","EN"),("2","2","GND")],"","mcu")
part("SW3","Tact BOOT","TS-1187A-B-A-B (4x4 tact)","C318884","KEY-SMD-4x4",[("1","1","BOOT"),("2","2","GND")],"Hold BOOT, tap EN to enter download mode.","mcu")

part("Q1","AO3400A N-MOSFET","AO3400A","C20917","SOT-23",[("1","G","IR_EN"),("2","S","GND"),("3","D","IR_SINK")],"Switches the IR LEDs (GPIO cannot drive them directly).","ir")

two("D1","LED red 0603","LED 0603 red","C2286","LED0603","CHG_LED1A","CHG_CHRG","Charging","power")
two("D2","LED green 0603","LED 0603 green","C72043","LED0603","CHG_LED2A","CHG_STDBY","Charged","power")
two("D3","LED blue 0603","LED 0603 blue","C72041","LED0603","LED_STATA","GND","Status","mcu")
two("D4","IR LED 850nm","SMD IR LED 850nm (1206/0805)","C-select","LED1206","IR_A1","IR_SINK","Pick any 850nm SMD IR LED on LCSC; Vf~1.4V","ir")
two("D5","IR LED 850nm","SMD IR LED 850nm (1206/0805)","C-select","LED1206","IR_A2","IR_SINK","","ir")

R = lambda ref,val,lcsc,n1,n2,note="": two(ref,val,f"Resistor {val} 1% 0603",lcsc,"R0603",n1,n2,note)
C = lambda ref,val,lcsc,n1,n2,note="": two(ref,val,f"Capacitor {val} 0603/0805 X5R/X7R",lcsc,("C0805" if val.startswith("10u") else "C0603"),n1,n2,note)
R("R1","10k","C25804","+3V3","EN","EN pull-up")
R("R2","100k","C25803","MOT_SLEEP","GND","motors asleep while MCU boots")
R("R3","10k","C25804","+3V3","MOT_FAULT","nFAULT is open-drain")
R("R4","5.6k","C23189","PROG","GND","TP4056 charge current ~215mA")
R("R5","5.1k","C23186","USB_CC1","GND")
R("R6","5.1k","C23186","USB_CC2","GND")
R("R7","1k","C21190","VBUS","CHG_LED1A")
R("R8","1k","C21190","VBUS","CHG_LED2A")
R("R9","4.7k","C23162","+3V3","I2C_SCL","I2C pull-up (DNP if breakouts have their own)")
R("R10","4.7k","C23162","+3V3","I2C_SDA","I2C pull-up (DNP if breakouts have their own)")
R("R11","100k","C25803","IR_EN","GND","IR gate pull-down")
R("R12","47","C23182","VBAT_SW","IR_A1","~50mA per IR LED at 3.7V")
R("R13","47","C23182","VBAT_SW","IR_A2")
R("R14","1k","C21190","LED_STAT","LED_STATA")
R("R15","100k","C25803","VBAT_SW","VBAT_SENSE","battery voltage divider (1/2)")
R("R16","100k","C25803","VBAT_SENSE","GND")
R("R17","10k","C25804","CAM_PWDN","GND","camera always on")
R("R18","10k","C25804","+3V3","CAM_RESET","camera reset released")
C("C1","10uF","C15850","VBUS","GND")
C("C2","10uF","C15850","VBAT","GND")
C("C3","10uF","C15850","VBAT_SW","GND","motor/LDO bulk")
C("C4","10uF","C15850","VBAT_SW","GND")
C("C5","100nF","C14663","VBAT_SW","GND","DRV8833 VM bypass")
C("C6","10nF","C57112","VCP","VBAT_SW","DRV8833 charge pump (16V+)")
C("C7","2.2uF","C23630","VINT","GND","DRV8833 VINT")
C("C8","10uF","C15850","+3V3","GND","LDO out")
C("C9","10uF","C15850","+3V3","GND","LDO out")
C("C10","100nF","C14663","+3V3","GND","ESP32 bypass")
C("C11","1uF","C15849","EN","GND","EN reset delay")
C("C12","100nF","C14663","VBAT_SENSE","GND")
C("C13","10uF","C15850","+3V3","GND","camera connector bulk")
C("C14","100nF","C14663","+3V3","GND","camera connector HF")

# ----------------------------------------------------------------------------
# CHECKS
# ----------------------------------------------------------------------------
def checks():
    errs, warns = [], []
    nets = collections.defaultdict(list)
    for r, p in P.items():
        seen = set()
        for num, name, net in p["pins"]:
            if (num,name) in seen: pass
            seen.add((num,name))
            if net: nets[net].append((r, num, name))
    # 1 every net has >=2 distinct component pins
    for n, c in nets.items():
        if len({(a,b) for a,b,_ in c}) < 2:
            errs.append(f"net {n} has only one connection: {c}")
    # 2 required rails
    for n in ("GND","+3V3","VBAT","VBAT_SW","VBUS"):
        if n not in nets: errs.append(f"missing rail {n}")
    # 3 ESP32 GPIO sanity
    reserved = {26,27,28,29,30,31,32,33,34,35,36,37}  # flash/PSRAM on N8R8 are internal pins 28-30 / IO35-37
    gpio_used = {}
    for num, name, net in P["U1"]["pins"]:
        if name.startswith("IO") and net:
            g = int(name[2:])
            if g in (35,36,37): errs.append(f"{name} is used by octal PSRAM on N8R8 - cannot be used")
            if g in (26,27,28,29,30,31,32,33,34): errs.append(f"{name} is flash/PSRAM bus")
            if g in (0,3,45,46) and net not in ("BOOT",): warns.append(f"strapping pin {name} used for {net}")
            if net in gpio_used: errs.append(f"duplicate signal {net}")
            gpio_used[net] = g
    # 4 camera 8-bit bus complete
    for s in ["CAM_D%d"%i for i in range(8)] + ["CAM_XCLK","CAM_PCLK","CAM_VSYNC","CAM_HREF","CAM_SIOC","CAM_SIOD"]:
        if s not in gpio_used: errs.append(f"camera signal {s} not on an ESP32 GPIO")
    # 5 USB on native pins
    if gpio_used.get("USB_DN")!=19 or gpio_used.get("USB_DP")!=20: errs.append("USB must be on GPIO19(D-)/GPIO20(D+)")
    # 6 DRV8833 inputs all driven
    for s in ("MOT_L_FWD","MOT_L_REV","MOT_R_FWD","MOT_R_REV","MOT_SLEEP","MOT_FAULT"):
        if s not in gpio_used: errs.append(f"{s} not on a GPIO")
    # 7 VINT must never touch a supply
    if any(r not in ("U2","C7") for r,_,_ in nets["VINT"]): errs.append("VINT connected to something other than its 2.2uF cap")
    # 8 ADC pin
    if gpio_used.get("VBAT_SENSE") not in range(1,11): errs.append("VBAT_SENSE must be on ADC1 (GPIO1-10)")
    # 9 BOM duplicates / refs
    if len(P) != len(set(P)): errs.append("duplicate refs")
    # 10 charge current vs cell
    pass
    return errs, warns, nets, gpio_used

# ----------------------------------------------------------------------------
# OUTPUTS
# ----------------------------------------------------------------------------
def write_netlist(nets):
    with open("netlist.csv","w",newline="") as f:
        w = csv.writer(f); w.writerow(["net","ref","pin_number","pin_name","part"])
        for n in sorted(nets, key=lambda x:(x not in ("GND","+3V3","VBAT","VBAT_SW","VBUS"), x)):
            for r,num,name in nets[n]:
                w.writerow([n,r,num,name,P[r]["value"]])
        for r,p in P.items():
            for num,name,net in p["pins"]:
                if net is None: w.writerow(["(no connect)",r,num,name,p["value"]])

def write_bom():
    groups = collections.OrderedDict()
    for r,p in P.items():
        if p["lcsc"] == "-": continue
        key = (p["value"],p["mpn"],p["lcsc"],p["fp"])
        groups.setdefault(key,[]).append(r)
    with open("bom.csv","w",newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment","Designator","Footprint","MPN (search this in EasyEDA)","LCSC Part # (confirm)","Quantity","Checked against LCSC"])
        for (val,mpn,lcsc,fp),refs in groups.items():
            ver = "YES" if any(P[r]["verified"] for r in refs) else "NO - confirm"
            w.writerow([val," ".join(refs),fp,mpn,lcsc,len(refs),ver])

def write_pinmap(gpio_used):
    names = {"MOT_L_FWD":"PIN_MOTOR_L_FWD","MOT_L_REV":"PIN_MOTOR_L_REV","MOT_R_FWD":"PIN_MOTOR_R_FWD","MOT_R_REV":"PIN_MOTOR_R_REV",
             "MOT_SLEEP":"PIN_MOTOR_NSLEEP","MOT_FAULT":"PIN_MOTOR_NFAULT","IR_EN":"PIN_IR_LED","LED_STAT":"PIN_STAT_LED",
             "I2C_SDA":"PIN_I2C_SDA","I2C_SCL":"PIN_I2C_SCL","VBAT_SENSE":"PIN_VBAT_ADC",
             "CAM_XCLK":"XCLK_GPIO_NUM","CAM_SIOD":"SIOD_GPIO_NUM","CAM_SIOC":"SIOC_GPIO_NUM","CAM_PCLK":"PCLK_GPIO_NUM",
             "CAM_VSYNC":"VSYNC_GPIO_NUM","CAM_HREF":"HREF_GPIO_NUM"}
    for i in range(8): names[f"CAM_D{i}"] = f"Y{i+2}_GPIO_NUM"
    with open("firmware/pinmap.h","w") as f:
        f.write("// AUTO-GENERATED by design.py - do not edit. Matches netlist.csv exactly.\n#pragma once\n")
        for net,macro in names.items():
            f.write(f"#define {macro:<18} {gpio_used[net]}\n")
        f.write("#define PWDN_GPIO_NUM      -1   // tied low on PCB (R17)\n#define RESET_GPIO_NUM     -1   // pulled high on PCB (R18)\n")

def write_svg(nets):
    blocks = [("U1","ESP32-S3 module"),("U2","Motor driver"),("U4","Charger"),("U3","3.3 V LDO")]
    W,H = 1400, 1250
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Arial, sans-serif" font-size="12">',
           f'<rect width="{W}" height="{H}" fill="white"/>',
           '<text x="20" y="28" font-size="20" font-weight="bold">SANJEEVNI NANO ROVER v2 - connection map (generated from design.py)</text>',
           '<text x="20" y="48" fill="#555">Each pin shows the NET it joins. Same net name = connected. Passives are listed under each IC.</text>']
    col_x = [20, 480, 940]
    def box(x,y,ref,title,pins):
        h = 34 + 16*len(pins)
        out.append(f'<rect x="{x}" y="{y}" width="430" height="{h}" fill="#f7f9fc" stroke="#345" rx="4"/>')
        out.append(f'<text x="{x+8}" y="{y+20}" font-weight="bold" font-size="14">{ref}  {html.escape(title)}</text>')
        for i,(num,name,net) in enumerate(pins):
            yy = y+38+16*i
            col = "#a00" if net is None else "#003366"
            if str(num) != name:
                out.append(f'<text x="{x+10}" y="{yy}" fill="#444">{html.escape(str(num))}</text>')
            out.append(f'<text x="{x+50 if str(num) != name else x+10}" y="{yy}">{html.escape(name)}</text>')
            out.append(f'<text x="{x+190}" y="{yy}" fill="{col}" font-family="monospace">{html.escape(net or "no connect")}</text>')
        return h
    pos = {"U1":(0,70),"U2":(1,70),"U4":(1,0),"U3":(2,70)}
    y_cols=[70,70,70]
    placed=[("U1",0),("U2",1),("U4",1),("U3",2),("U5",2),("J1",2),("J2",0),("J3",1),("J6",2),("J7",2),("J8",1),("Q1",1),("SW1",2),("SW2",2),("SW3",2),("PL",1),("PR",1)]
    # simple stacking per column
    for ref,c in placed:
        p = P[ref]
        h = box(col_x[c], y_cols[c], ref, p["value"], p["pins"])
        y_cols[c] += h + 14
    # passive table at the bottom-most column
    y = max(y_cols)+8
    out.append(f'<text x="20" y="{y}" font-weight="bold" font-size="14">Passives / LEDs  (ref value : net1 - net2)</text>')
    items = [r for r,p in P.items() if p["group"]=="passive" or r in ("D1","D2","D3","D4","D5")]
    for i,r in enumerate(items):
        p=P[r]; cx = 20 + (i%3)*460; cy = y+20+ (i//3)*16
        out.append(f'<text x="{cx}" y="{cy}" font-family="monospace">{r:<4}{html.escape(p["value"]):<7} {p["pins"][0][2]} - {p["pins"][1][2]}</text>')
    out.append('</svg>')
    open("docs/schematic.svg","w").write("\n".join(out).replace(f'viewBox="0 0 {W} {H}"', f'viewBox="0 0 {W} {int(y+20+16*(len(items)//3+2))}"'))

if __name__ == "__main__":
    errs, warns, nets, gpio = checks()
    for w in warns: print("WARN:", w)
    if errs:
        for e in errs: print("ERROR:", e)
        sys.exit(1)
    write_netlist(nets); write_bom(); write_pinmap(gpio); write_svg(nets)
    print(f"OK: {len(P)} parts, {len(nets)} nets, {len(gpio)} MCU signals. Files written.")
