-- ============================================================================
-- SANJEEVNI: Disaster-Aware Dynamic Routing & Hospital Gateway
-- IBM Db2 Enterprise Relational Database Schema & DDL
-- Compatible with: IBM Db2 LUW, IBM Db2 on Cloud, IBM Db2 Developer Extension
-- Team: Aparajit (अपराजित) | Hackathon Module 2
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. TABLE: SANJEEVNI_HOSPITALS
-- Stores emergency trauma centers, real-time ICU capacities & life-support stock.
-- ----------------------------------------------------------------------------
CREATE TABLE SANJEEVNI_HOSPITALS (
    HOSPITAL_ID         INTEGER         NOT NULL GENERATED ALWAYS AS IDENTITY (START WITH 101, INCREMENT BY 1),
    HOSPITAL_NAME       VARCHAR(120)    NOT NULL,
    CITY                VARCHAR(60)     NOT NULL,
    LATITUDE            DECIMAL(9, 6)   NOT NULL,
    LONGITUDE           DECIMAL(9, 6)   NOT NULL,
    TOTAL_ICU_BEDS      INTEGER         NOT NULL DEFAULT 30,
    AVAILABLE_ICU_BEDS  INTEGER         NOT NULL DEFAULT 15,
    VENTILATORS_ACTIVE  INTEGER         NOT NULL DEFAULT 10,
    BLOOD_UNITS_ONEG    INTEGER         NOT NULL DEFAULT 8,
    O2_PURITY_PCT       DECIMAL(4, 1)   NOT NULL DEFAULT 98.0,
    STATUS              VARCHAR(20)     NOT NULL DEFAULT 'Operational',
    LAST_UPDATED        TIMESTAMP       NOT NULL DEFAULT CURRENT TIMESTAMP,
    CONSTRAINT PK_HOSPITALS PRIMARY KEY (HOSPITAL_ID),
    CONSTRAINT CHK_ICU_CAPACITY CHECK (AVAILABLE_ICU_BEDS <= TOTAL_ICU_BEDS AND AVAILABLE_ICU_BEDS >= 0)
);

-- ----------------------------------------------------------------------------
-- 2. TABLE: SANJEEVNI_MISSIONS
-- Disaster casualty triage & emergency ambulance dispatch audit trail.
-- ----------------------------------------------------------------------------
CREATE TABLE SANJEEVNI_MISSIONS (
    MISSION_ID          VARCHAR(32)     NOT NULL,
    AMBULANCE_CALLSIGN  VARCHAR(24)     NOT NULL,
    ORIGIN_NAME         VARCHAR(120)    NOT NULL,
    ORIGIN_LAT          DECIMAL(9, 6)   NOT NULL,
    ORIGIN_LNG          DECIMAL(9, 6)   NOT NULL,
    DESTINATION_NAME    VARCHAR(120)    NOT NULL,
    DESTINATION_LAT     DECIMAL(9, 6)   NOT NULL,
    DESTINATION_LNG     DECIMAL(9, 6)   NOT NULL,
    DISTANCE_KM         DECIMAL(6, 2)   NOT NULL,
    EST_TIME_MINS       INTEGER         NOT NULL,
    ROUTE_CORRIDOR      VARCHAR(30)     NOT NULL DEFAULT 'Safe Detour (A*)',
    HAZARD_BYPASSED     VARCHAR(120),
    STATUS              VARCHAR(20)     NOT NULL DEFAULT 'Dispatched',
    CREATED_AT          TIMESTAMP       NOT NULL DEFAULT CURRENT TIMESTAMP,
    COMPLETED_AT        TIMESTAMP,
    CONSTRAINT PK_MISSIONS PRIMARY KEY (MISSION_ID)
);

-- ----------------------------------------------------------------------------
-- 3. TABLE: SANJEEVNI_HAZARDS
-- Verified road cut-offs, submerged bridges, and landslide choke points.
-- ----------------------------------------------------------------------------
CREATE TABLE SANJEEVNI_HAZARDS (
    HAZARD_ID           INTEGER         NOT NULL GENERATED ALWAYS AS IDENTITY (START WITH 501, INCREMENT BY 1),
    HAZARD_TITLE        VARCHAR(140)    NOT NULL,
    HAZARD_TYPE         VARCHAR(30)     NOT NULL, -- 'Flood', 'Landslide', 'Road Collapse'
    SEVERITY            VARCHAR(15)     NOT NULL, -- 'Critical', 'High', 'Medium'
    CITY_CORRIDOR       VARCHAR(80)     NOT NULL,
    LATITUDE            DECIMAL(9, 6)   NOT NULL,
    LONGITUDE           DECIMAL(9, 6)   NOT NULL,
    REPORTED_AT         TIMESTAMP       NOT NULL DEFAULT CURRENT TIMESTAMP,
    STATUS              VARCHAR(20)     NOT NULL DEFAULT 'Active',
    VERIFIED_SOURCE     VARCHAR(60)     NOT NULL DEFAULT 'TinyFish Real-Time Scraper',
    CONSTRAINT PK_HAZARDS PRIMARY KEY (HAZARD_ID)
);

-- ----------------------------------------------------------------------------
-- 4. TABLE: SANJEEVNI_HOTSPOTS
-- Multi-hazard predictive risk scoring from Sanjeevni-DisasterNet AI engine.
-- ----------------------------------------------------------------------------
CREATE TABLE SANJEEVNI_HOTSPOTS (
    HOTSPOT_ID          VARCHAR(20)     NOT NULL,
    HOTSPOT_NAME        VARCHAR(120)    NOT NULL,
    HAZARD_TYPE         VARCHAR(60)     NOT NULL,
    PROBABILITY_PCT     INTEGER         NOT NULL,
    SEVERITY            VARCHAR(15)     NOT NULL,
    TIME_WINDOW         VARCHAR(40)     NOT NULL,
    LATITUDE            DECIMAL(9, 6)   NOT NULL,
    LONGITUDE           DECIMAL(9, 6)   NOT NULL,
    STAGING_HOSPITAL    VARCHAR(120)    NOT NULL,
    RISK_TELEMETRY      VARCHAR(255)    NOT NULL,
    LAST_INFERENCE_AT   TIMESTAMP       NOT NULL DEFAULT CURRENT TIMESTAMP,
    CONSTRAINT PK_HOTSPOTS PRIMARY KEY (HOTSPOT_ID)
);

-- ============================================================================
-- SEED INITIAL DATA FOR LIVE HACKATHON DEMONSTRATION
-- ============================================================================

-- Hospitals Registry
INSERT INTO SANJEEVNI_HOSPITALS (HOSPITAL_NAME, CITY, LATITUDE, LONGITUDE, TOTAL_ICU_BEDS, AVAILABLE_ICU_BEDS, VENTILATORS_ACTIVE, BLOOD_UNITS_ONEG, O2_PURITY_PCT, STATUS)
VALUES 
('Kailash Hospital & Heart Institute', 'Noida', 28.5833, 77.3333, 30, 18, 14, 14, 98.5, 'Operational'),
('ESI Hospital', 'Noida', 28.5950, 77.3350, 30, 30, 16, 20, 99.1, 'Operational'),
('Fortis Hospital', 'Noida', 28.6186, 77.3725, 25, 0, 2, 3, 91.0, 'Full Capacity'),
('AIIMS Rishikesh Trauma Center', 'Rishikesh', 30.1158, 78.2900, 30, 18, 14, 14, 99.4, 'Operational'),
('AIIMS New Delhi Apex Trauma', 'New Delhi', 28.5668, 77.2078, 60, 35, 28, 32, 99.8, 'Operational'),
('District Civil Hospital', 'Uttarkashi', 30.7268, 78.4354, 12, 0, 2, 2, 88.0, 'Full Capacity');

-- Initial Missions Audit Log
INSERT INTO SANJEEVNI_MISSIONS (MISSION_ID, AMBULANCE_CALLSIGN, ORIGIN_NAME, ORIGIN_LAT, ORIGIN_LNG, DESTINATION_NAME, DESTINATION_LAT, DESTINATION_LNG, DISTANCE_KM, EST_TIME_MINS, ROUTE_CORRIDOR, HAZARD_BYPASSED, STATUS)
VALUES
('MSN-8801', 'MEDIC-01', 'Noida, Uttar Pradesh', 28.5800, 77.3300, 'ESI Hospital', 28.5950, 77.3350, 6.60, 10, 'Direct Corridor', NULL, 'Completed'),
('MSN-8802', 'MEDIC-04', 'Noida Sector 62', 28.6169, 77.3735, 'Ghaziabad Inundation Zone', 28.6692, 77.4538, 23.10, 25, 'Safe Detour (A*)', 'NH-9 Waterlogging Underpass', 'Completed'),
('MSN-8803', 'DISPATCH-09', 'Noida, Uttar Pradesh', 28.5800, 77.3300, 'Garhwal Tectonic Thrust', 30.4500, 78.4200, 339.60, 288, 'Safe Detour (A*)', 'Main Central Thrust Subsidence', 'Dispatched');

-- Active Verified Hazards
INSERT INTO SANJEEVNI_HAZARDS (HAZARD_TITLE, HAZARD_TYPE, SEVERITY, CITY_CORRIDOR, LATITUDE, LONGITUDE, VERIFIED_SOURCE)
VALUES
('Ghaziabad Arterial Underpass Flooded', 'Flood', 'Critical', 'Ghaziabad, Uttar Pradesh', 28.6692, 77.4538, 'TinyFish Live Web Scraper'),
('Sector 95 Submerged Vehicle Inundation', 'Flood', 'High', 'Sector 95 Underpass, Noida', 28.5360, 77.3880, 'Municipal Traffic Bulletin'),
('Bhagirathi Bridge Submerged 1.2m', 'Flood', 'Critical', 'NH-34 Dharasu Corridor', 30.6500, 78.3800, 'State Disaster Control Room');

-- AI Predicted Hotspots
INSERT INTO SANJEEVNI_HOTSPOTS (HOTSPOT_ID, HOTSPOT_NAME, HAZARD_TYPE, PROBABILITY_PCT, SEVERITY, TIME_WINDOW, LATITUDE, LONGITUDE, STAGING_HOSPITAL, RISK_TELEMETRY)
VALUES
('PRED-01', 'Garhwal Tectonic Thrust & Tehri Ridge', 'Seismic Strain & Slope Failure', 88, 'Critical', 'Next 6 - 18 Hours', 30.4500, 78.4200, 'AIIMS Rishikesh', 'Gutenberg-Richter b-value 0.79 dip, strain: 18.2 mm/yr'),
('PRED-02', 'Yamuna & Hindon Floodplain Basin', 'Flash Inundation & Road Cutoff', 82, 'High', 'Next 12 - 24 Hours', 28.5600, 77.3400, 'Kailash Hospital & Heart Institute', 'Pressure gradient -4.2 hPa, drainage sat: 92%'),
('PRED-03', 'Delhi-Haridwar Ridge / Rohtak Fault', 'Subsurface Structural Tremor', 74, 'High', 'Next 24 - 48 Hours', 28.8955, 76.6066, 'AIIMS New Delhi', 'Foreshock swarm cluster, 1.8x amplification'),
('PRED-04', 'Chamba-Mussoorie Slope Cutting (NH-34)', 'Landslide & Rockfall Debris', 69, 'Elevated', 'Next 8 - 14 Hours', 30.5145, 78.3908, 'District Civil Hospital', 'Mohr-Coulomb Factor of Safety: 0.91');
