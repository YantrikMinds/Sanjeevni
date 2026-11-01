# ⚡ Sanjeevni — Disaster-Aware Dynamic Routing, Hospital Gateway & AI Disaster Predictor
> **Team Aparajit (अपराजित) | Hackathon Module 2**

Sanjeevni is an intelligent, low-bandwidth, multi-hazard emergency navigation and disaster response platform built to ensure ambulances and first responders never get trapped in flooded underpasses, collapsed bridges, or landslide debris.

---

## 🚀 Quick Start (How to Run)

### Requirements:
- **Node.js** (v18 or higher installed on Windows, Mac, or Linux)
- A modern web browser (Chrome, Edge, Firefox, Brave)
- **Zero npm dependencies required!** (Runs with 100% native built-in Node modules)

### Steps to Run:
1. Open terminal or PowerShell in this folder:
   ```bash
   node server.js
   ```
2. Open your web browser and navigate to:
   ```
   http://localhost:3000
   ```
3. That's it! Sanjeevni will automatically detect your live location, connect to live USGS seismic feeds, OpenWeather telemetry, and TinyFish local municipal scrapers.

---

## 🌟 Key Features

1. **IBM Db2 Enterprise Relational Service & VS Code Developer Extension:**
   - **Schema & DDL:** Standard IBM Db2 tables (`SANJEEVNI_HOSPITALS`, `SANJEEVNI_MISSIONS`, `SANJEEVNI_HAZARDS`, `SANJEEVNI_HOTSPOTS`) in `scripts/init_db2.sql`.
   - **ACID Row-Level Bed Locking:** Prevents race conditions where two dispatched ambulances book the same remaining ICU bed simultaneously during disaster triage (`/api/db2/reserve`).
   - **Disaster Mission Audit Ledger:** Immutable audit trail of every ambulance route dispatched, hazard bypassed, and triage state committed (`/api/reports`).
   - **VS Code Extension Demo:** Ready-to-run demo queries in `scripts/demo_queries.sql` showcasing Db2 syntax, spatial radius search, and ICU vacancy filtering directly in the VS Code editor!

2. **AI Disaster Prediction Engine (`/api/predict` & Predictor View):**
   - Multi-hazard heuristic model monitoring Gutenberg-Richter $b$-value dips, crustal strain accumulation ($18.2\text{ mm/yr}$), barometric pressure drops ($-4.2\text{ hPa}$), and slope shear safety factors.
   - 4 active vulnerability hotspots predicted in Northern India (Garhwal Tectonic Thrust, Yamuna Floodplain Basin, Rohtak Fault, Chamba Slope Cutting).
   - **1-Click Rescue Route Deployment (`🚨 Plan Route`)**: Automatically sets Origin = Live Location, Destination = Disaster Hotspot, and calculates real OSRM road driving route with turn-by-turn navigation steps.
   - **Interactive Scenario Simulation**: Test tectonic stress surges (+9% probability) or cloudburst inundation anomalies (+12%).

2. **Disaster-Aware Dynamic Routing (OSRM + A\* Detour):**
   - Blue line: Direct corridor.
   - Green line: Dynamic Safe Detour bypassing blocked or flooded infrastructure.
   - Red dashed line: Blocked/inundated road segment.
   - Turn-by-turn driving steps with elevation profile visualization.

3. **Intelligent Hazard Detour from Live Alerts:**
   - Real-time road blockage alerts parsed from TinyFish local web scraper.
   - Clicking `"Route Around Hazard"` automatically extracts the exact disaster site (e.g. `Ghaziabad, Uttar Pradesh` or `Sector 95 Underpass, Noida`), sets it as destination, and highlights the safe bypass route!

4. **Emergency Hospital Gateway:**
   - Real hospital discovery near user.
   - Live ICU bed vacancy tracking, operational ventilators, and O- negative blood bank units.
   - Filter toggle for operational ICU beds and 1-click `"Route Here"` navigation.

5. **Safe Evacuation Return Route:**
   - Calculates evacuation corridor from disaster ground zero back to emergency base camp.

6. **Live USGS Seismic Tracker:**
   - 25 global and regional seismic events tracked in real time.
   - Dynamic Haversine distance in KM from user's live position.
   - 1-click map centering on any tremor.

---

## 🛠️ Architecture & Tech Stack

- **Frontend:** Vanilla JavaScript (ES6+), Semantic HTML5, CSS3 Variables, Leaflet.js (ArcGIS World Topo Hillshade & Satellite layers).
- **Backend:** Node.js native HTTP server (`server.js`) with IBM Db2 relational service layer (`lib/db2.js`), reverse-proxy caching, and CORS bypass.
- **Enterprise Database:** IBM Db2 Developer Extension (VS Code) + Db2 DRDA/REST protocol integration.
- **APIs & Services Connected:**
  - **IBM Db2:** ACID concurrency lock for ICU triage & mission telemetry audit.
  - **OpenWeatherMap API:** Live atmospheric pressure, temp, humidity, wind.
  - **USGS Global Earthquake Hazards Feed:** Real-time seismic GeoJSON stream.
  - **TinyFish Scraper API:** Local municipal traffic, flood, and road blockage reports.
  - **OSRM (Open Source Routing Machine):** Real turn-by-turn driving road network.
  - **Nominatim / IP Geolocation:** Reverse geocoding & live location detection.

---

## 📁 Directory Structure
```
sanjeevni-routing-dashboard/
├── index.html                  # Main SPA Shell, Topbar & Db2 Status Pill
├── styles.css                  # Design System, Responsive & Db2 Styling
├── app.js                      # Core Application Controller & State
├── api.js                      # Unified API Client Service (with Db2 endpoints)
├── config.js                   # API Keys & Endpoints Configuration
├── server.js                   # Node.js Server + IBM Db2 REST Endpoints
├── lib/
│   └── db2.js                  # IBM Db2 Relational Engine & ACID Lock Service
├── scripts/
│   ├── init_db2.sql            # Full IBM Db2 DDL Schema & Seed Records
│   └── demo_queries.sql        # 5 Native Db2 Demo Queries for VS Code Extension
├── comprehensive_verification.js # 24-point Automated Audit Script
├── test_endpoints.js           # API Endpoints Health Check
├── test_hazard_routing.js      # Hazard Detour Verification Script
├── deep_stress_test.js         # 14-point Stress & Edge-Case Audit
└── README.md                   # This Documentation
```

*Built with ❤️ by Team Aparajit (अपराजित)*
