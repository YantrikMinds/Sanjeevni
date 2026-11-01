# ⚡ SANJEEVNI (संजीवनी)
### Autonomous Sub-5cm USAR Disaster Robotics & Tactical Fleet Tele-Op Platform
**Developed by Team Aprajit (@YantrikMinds)**  
*Nishant Pathak (Lead Architect) • Md Hammaduddin • Aanya Pathak*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: ESP32-S3](https://img.shields.io/badge/Hardware-ESP32--S3%20Octal%20PSRAM-orange)](hardware_pcb/)
[![Status: Hackathon 3rd Place Winner](https://img.shields.io/badge/Award-3rd%20Place%20Winner-brightgreen)](#)
[![Python 3.10+](https://img.shields.io/badge/Backend-Python%203-blue)](server.py)

---

## 📌 Overview

**Sanjeevni** is an end-to-end tactical Urban Search and Rescue (USAR) robotics platform designed to penetrate pancake and cantilever collapse voids where humans, search dogs, and full-sized rovers cannot enter.

The platform combines:
1. **Sub-5cm Rubble Scout Nano-Rover Hardware**: An ultra-compact $46\text{ mm} \times 48\text{ mm} \times 22\text{ mm}$ invertible dual-drive robot carrier powered by an ESP32-S3 with dual-port streaming.
2. **Tactical War Room Command Dashboard**: Live multi-phone and hardware rover video feeds, real-time WASD tele-operation cockpit, environmental telemetry, and survivor alert feeds.
3. **AI Survivor Detection & Triage Intelligence**: Vision-based pose estimation for prone/trapped victims with automated SBAR incident reports.
4. **IBM Db2 Enterprise Incident Layer**: High-reliability SQL schema and analytics queries for mission auditing and rescue coordination.

---

## 🛠️ System Architecture

```
                      [ DISASTER ZONE (RUUBLE VOID) ]
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           ▼                                                   ▼
   [Sanjeevni Nano-Rover]                             [Mobile Fleet Scout]
  • Sub-5cm Invertible PCB                           • Android / iOS Device
  • ESP32-S3 8MB Octal PSRAM                         • MoveNet Edge Inference
  • OV2640 160° Night-Vision Camera                  • Flashlight / Sensor Node
  • DRV8833 Dual Silent 20kHz PWM                    • WebRTC / HTTPS Stream
  • VL53L1X Laser LiDAR + MPU6050                    • 1080p Video Feed
           │                                                   │
           └─────────────────────────┬─────────────────────────┘
                                     │ Wi-Fi Mesh / REST + MJPEG
                                     ▼
                      [ SANJEEVNI FIELD GATEWAY ]
                             (server.py)
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           ▼                                                   ▼
   [Tactical Dashboard]                               [IBM Db2 Audit Layer]
  • Live Multi-Cam HUD                              • Mission & Sector Records
  • WASD Direct Tele-Op                             • Survivor Triage Queue
  • Gas & Tilt Telemetry                            • USAR Deployment History
  • 1-Click USAR Squad Dispatch
```

---

## 📁 Repository Structure

```
Sanjeevni/
├── dashboard.html             # Tactical War Room Command HUD with WASD driving cockpit
├── rover.html                 # Mobile-first smart rover client (phone sensors + camera)
├── server.py                  # Dual-protocol HTTP/HTTPS tactical gateway & tele-op bridge
├── dynamic_routing_map.html   # Sector hazard map & survivor location routing
├── 3d_collapse_simulation.html# Three.js 3D structural collapse simulation
├── static/                    # MoveNet / TensorFlow.js offline models & assets
├── hardware_pcb/              # Hardware engineering files & Schematics
│   ├── v2_audited/            # 100% Audited production hardware package
│   │   ├── design.py          # Single source of truth & electrical rules engine
│   │   ├── bom.csv            # Production BOM with MPN & LCSC references
│   │   ├── netlist.csv        # Complete circuit netlist
│   │   ├── docs/schematic.svg # Visual vector schematic connection map
│   │   ├── docs/AUDIT.md      # Full engineering audit and bug fix log
│   │   └── firmware/          # Dual-port FreeRTOS ESP32-S3 firmware
│   │       ├── sanjeevni_nano.ino
│   │       └── pinmap.h
│   └── README_EASYEDA_IMPORT.md # Guide to import & manufacture with JLCPCB
└── ibm_db2/                   # Enterprise database extensions
    ├── schema_db2.sql         # Production tables & constraints
    ├── queries_db2.sql        # Analytics & triage queries
    └── demo_sample_data.sql   # Real disaster exercise seed data
```

---

## 🚀 Quick Start Guide

### 1. Launch the Tactical Gateway
```bash
python3 server.py
```
* **War Room Dashboard:** Open `http://localhost:8080/` in your browser.
* **Phone Rover Client:** Scan QR or navigate to `https://<YOUR-IP>:8443/rover` on any smartphone.

### 2. Tele-Operation Controls
* **[W] / [↑]**: Forward Crawl
* **[S]** / **[↓]**: Reverse
* **[A]** / **[←]**: Pivot Left
* **[D]** / **[→]**: Pivot Right
* **[Spacebar]**: Emergency Brake
* **Speed Selectors**: Crawl (35%), Traverse (70%), Sprint (100%)
* **IR Torch**: Toggle front night-vision illuminators

---

## 🤖 Nano-Rover Hardware Specs

| Metric | Specification |
| :--- | :--- |
| **Dimensions** | $46.0\text{ mm (L)} \times 48.0\text{ mm (W)} \times 22.0\text{ mm (H)}$ (Strict Sub-5cm) |
| **Microcontroller** | ESP32-S3-WROOM-1-N8R8 (Dual-core 240MHz, 8MB Octal PSRAM) |
| **Motor Driver** | Texas Instruments DRV8833PWPR Dual H-Bridge (1.5A per channel) |
| **Power Regulation** | Diodes Inc AP2112K-3.3 (Ultra-Low Dropout 250mV @ 600mA) |
| **Battery & Charge** | 3.7V 400mAh LiPo via TP4056 with safe 215mA charge regulation |
| **Optical System** | OV2640 2.0MP 160° Wide-Angle Fisheye + Dual 850nm IR LEDs |
| **Sensors** | VL53L1X ToF Laser (4m range) + MPU-6050 6-Axis Gyro/Accelerometer |
| **Firmware Design** | Port 80 Control Server + Port 81 Dedicated FreeRTOS MJPEG Stream |

---

## 👥 Authors & Team Aprajit

* **Nishant Pathak** ([@YantrikMinds](https://github.com/YantrikMinds)) — Project Lead, Embedded Systems, Hardware & PCB Design
* **Md Hammaduddin** — Robotics Simulation, Sensor Systems & Mechanics
* **Aanya Pathak** — AI Vision Pipeline, Triage Logic & Telemetry Analytics

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
