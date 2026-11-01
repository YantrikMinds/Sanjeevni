# 🛠️ SANJEEVNI NANO ROVER AIO BOARD v1.0 — EasyEDA Import Guide
**Dimensions:** 46.0 mm × 48.0 mm (Strict Sub-5cm Envelope)  
**Target:** 2-5 cm Rubble Scout Autonomous Robot Carrier  
**Designed by:** Team Aprajit (Nishant Pathak)

---

## 🚀 1. EasyEDA Me Kaise Import Karna Hai? (Step-by-Step)

### Method A: Direct File Import (Sabse Aasan)
1. Browser me **EasyEDA Web Editor** kholo:  
   👉 **[https://easyeda.com/editor](https://easyeda.com/editor)**
2. Upar menu me click karo:  
   **File ➡️ Import...**
3. Popup window me:
   * Select karo: **"EasyEDA"** ya **"KiCad"**
   * Browse karke humari file select karo:  
     📂 `/home/ece/.gemini/antigravity/scratch/sanjeevni/hardware_pcb/sanjeevni_nano_rover.kicad_sch` (ya `.json`)
4. **"Import"** par click karo.
5. Boom! Tumhara schematic canvas par open ho jayega!

---

## ⚡ 2. COMPLETE PINOUT & WIRING TABLE (Netlist Reference)

Ye table tumhare paas rahegi to EasyEDA me 2 minute me verify ho jayega ki kaunsa taar kahan judna hai:

### A) Microcontroller (ESP32-S3) ➡️ Motor Driver (DRV8833):
| ESP32-S3 Pin | Function | DRV8833 Pin | Description |
| :--- | :--- | :--- | :--- |
| **GPIO 4** | PWM / Digital OUT | **IN1** | Left Motor Forward Drive |
| **GPIO 5** | PWM / Digital OUT | **IN2** | Left Motor Reverse Drive |
| **GPIO 6** | PWM / Digital OUT | **IN3** | Right Motor Forward Drive |
| **GPIO 7** | PWM / Digital OUT | **IN4** | Right Motor Reverse Drive |
| **3V3** | Logic High | **nSLEEP** | Pull-up via 10k resistor (Enables Driver) |
| **GND** | Ground | **GND, AISEN, BISEN** | Current Sense Ground |
| **VBAT_SW** | Battery Power (3.7V - 4.2V) | **VM, VINT** | High-Current Motor Power |
| **OUT1, OUT2** | Motor Output | **J4 Screw Terminal** | To Left N20 Micro-Motor |
| **OUT3, OUT4** | Motor Output | **J5 Screw Terminal** | To Right N20 Micro-Motor |

---

### B) ESP32-S3 ➡️ Sensors (I2C Bus):
| ESP32-S3 Pin | Function | Sensor Connected |
| :--- | :--- | :--- |
| **GPIO 17** | I2C SCL (Clock) | Pin 3 of VL53L1X ToF Laser + MPU6050 Gyro |
| **GPIO 18** | I2C SDA (Data) | Pin 4 of VL53L1X ToF Laser + MPU6050 Gyro |
| **GPIO 15** | Digital OUT (MOSFET) | Front High-Power SMD Infrared (IR) LEDs (Night Vision) |
| **GPIO 16** | Digital OUT | Onboard Status Indicator LED |

---

### C) ESP32-S3 ➡️ OV2640 Ribbon Camera (24-Pin FPC):
| ESP32-S3 Pin | Camera Signal | Description |
| :--- | :--- | :--- |
| **GPIO 38** | **XCLK** | System Reference Clock |
| **GPIO 39** | **PCLK** | Pixel Data Clock |
| **GPIO 40** | **VSYNC** | Vertical Frame Sync |
| **GPIO 41** | **HREF** | Horizontal Line Sync |
| **GPIO 10 - 14, 21, 47, 48** | **D0 - D7** | 8-Bit Parallel Video Pixel Bus |
| **GPIO 1, 2** | **SIOD, SIOC** | I2C Camera Configuration Bus |

---

### D) Power & Battery Subsystem (USB-C + TP4056 + AMS1117-3.3):
| Component | From | To | Spec |
| :--- | :--- | :--- | :--- |
| **USB-C Port (J1)** | External 5V Charger | TP4056 Pin 4 (VCC) | CC1/CC2 tied to GND with 5.1k |
| **TP4056 (U4)** | Pin 5 (BAT) | JST-PH 2.0mm Battery Jack (J3) | 1A Charging via 1.2k on PROG pin |
| **Battery Switch (SW1)** | J3 (+VBAT) | VBAT_SW (Switched Power Rail) | Power ON/OFF Toggle |
| **AMS1117-3.3 (U3)** | VBAT_SW | +3V3 System Rail | Powers ESP32, Camera, Sensors |

---

## 📐 3. SCHEMATIC SE PCB ME KAISE BADALNA HAI? (Convert to PCB)

EasyEDA me schematic open karne ke baad:

1. Top bar par click karo: **Design ➡️ Convert Schematic to PCB**.
2. **Set Board Dimensions**:
   * Width: **48.0 mm** (Wheel-to-wheel fit)
   * Height: **46.0 mm** (Length)
   * Corner Radius: **3.0 mm** (Rounded corners so it doesn't get stuck in rubble)
   * Layers: **2 Layers** (Top & Bottom Copper)
3. **Components Placement**:
   * **Front edge**: OV2640 Camera connector aur IR LEDs.
   * **Center**: ESP32-S3 Chip aur DRV8833 Motor Driver.
   * **Rear edge**: USB-C Port, Slide Switch aur Battery JST connector.
   * **Left/Right edges**: Motor terminals.
4. **Auto-Route Tracks**:
   * Click **Route ➡️ Auto Router**.
   * Power tracks width: **0.8 mm** (Motors ke liye mota track).
   * Signal tracks width: **0.25 mm** (Data ke liye).
   * Click **Run** — EasyEDA 15 second me saare copper tracks bina kisi galti ke route kar dega!
5. **View 3D Model**:
   * Click **View ➡️ 3D View**.
   * Tumhe apna chhota 4.6cm × 4.8cm board chamchamata hua 3D me dikhai dega!

---

## 📦 4. BOM (Bill of Materials) & Ordering
Sabhi components ke exact **LCSC Part Numbers** file `bom_sanjeevni_nano.csv` me save hain. JLCPCB ya LionCircuits par upload karte hi sabhi chips automatic pre-select ho jayengi!
