# 🚀 IBM Db2 Developer Extension — Hackathon Bonus Track Guide
**Project:** SANJEEVNI (Team Aprajit)  
**Track:** IBM Db2 Database Development Integration in Visual Studio Code (VS Code)

---

## 🎯 1. Hackathon Me Judges Ko Kya Bolna Hai?
Jab judges puchein: *"Aapne IBM Db2 kaise use kiya hai?"*, to ye bolna:

> **"Sir/Ma'am, Sanjeevni produces real-time disaster telemetry from our edge scout rovers (Moto G62 & iPhone 13).**  
> **For enterprise disaster command, compliance auditing, and hospital bed triage, we architected our complete relational database on IBM Db2 for Linux, UNIX, and Windows (LUW).**  
> **Using the official IBM Db2 Developer Extension in VS Code, we manage our schemas (`SANJEEVNI_FLEET`, `SANJEEVNI_SURVIVORS`, `SANJEEVNI_SECTORS`), execute mission-critical triage queries, inspect LOB data, and maintain UN INSARAG cryptographic audit trails."**

---

## 💻 2. VS Code Me Kaise Setup Karna Hai? (Aanya / Hammad ke Windows Laptop par - 2 Minutes)

Kyunki Aanya aur Hammad ke paas Windows laptops hain jinpe VS Code chal raha hai:

### Step 1: Install Extension in VS Code
1. VS Code open karo.
2. Left side par **Extensions** icon dabao (ya `Ctrl + Shift + X`).
3. Search bar me type karo: **`IBM Db2 Developer Extension`** (Publisher: IBM).
4. **Install** par click karo.

### Step 2: Open Sanjeevni's Db2 Files
1. VS Code me `sanjeevni/ibm_db2/` folder open karo.
2. Ye 3 files dekho:
   - **`schema_db2.sql`**: Production IBM Db2 DDL schema.
   - **`demo_sample_data.sql`**: Moto G62 + iPhone 13 live telemetry inserts.
   - **`queries_db2.sql`**: 4 High-impact disaster triage and fleet queries.

### Step 3: Features Jo Judges Ko Dikhani Hain (Extension Highlights)
1. **Db2 Syntax Highlighting & Validation**:
   - `schema_db2.sql` open karo. Extension Db2 keywords (`GENERATED ALWAYS AS IDENTITY`, `CURRENT TIMESTAMP`, `VARCHAR`) ko native Db2 color theme me render karta hai.
2. **SQL Formatting**:
   - Right click karo ➡️ **Format Document** (Db2 extension automatically indents and formats the SQL).
3. **Db2 Connections View**:
   - Left Activity Bar me **DB2** icon appear hoga.
   - Wahan `DB2 CONNECTIONS` view dikhata hai.
   - Agar local instance create karna hai: Click **"Create Db2 Instance"** ya connect to IBM Cloud Db2.
   - Agar container nahi chalana: Sirf VS Code editor me `.sql` files open karke syntax validation, IntelliSense code completion aur query structure show kar do!

---

## 📊 3. Database Schema Overview:

1. **`SANJEEVNI_FLEET`**:
   - Stores each rover's hardware state (`NODE_ID`, `MODEL`, `BATTERY_PCT`, `IMU_TILT_DEG`, `CH4_METHANE_PPM`, `VOID_CLEARANCE_M`).
2. **`SANJEEVNI_SECTORS`**:
   - Maps disaster collapse pattern (`PANCAKE`, `LEAN_TO`, `CANTILEVER`) and coordinates.
3. **`SANJEEVNI_SURVIVORS`**:
   - Logs edge vision detections (`CONFIDENCE_PCT`, `DETECTED_LAT`, `DETECTED_LNG`, `STATUS`).
4. **`SANJEEVNI_DISPATCH_LOG`**:
   - UN INSARAG compliant cryptographic sign-off (`SIGN_OFF_HASH`, `COMMANDER_NAME`).
