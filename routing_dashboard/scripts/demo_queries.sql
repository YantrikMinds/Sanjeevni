-- ============================================================================
-- SANJEEVNI - IBM Db2 Live Demonstration SQL Queries
-- Use this script in VS Code with the IBM Db2 Developer Extension
-- Right-click anywhere in this editor and select "Run Query" (or Ctrl + Enter)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- QUERY 1: Real-time Emergency Mission Audit Trail
-- Proves that ambulance dispatches from Sanjeevni are persisted in IBM Db2
-- ----------------------------------------------------------------------------
SELECT 
    MISSION_ID,
    AMBULANCE_CALLSIGN,
    ORIGIN_NAME,
    DESTINATION_NAME,
    DISTANCE_KM,
    EST_TIME_MINS,
    ROUTE_CORRIDOR,
    STATUS,
    CREATED_AT
FROM SANJEEVNI_MISSIONS
ORDER BY CREATED_AT DESC;


-- ----------------------------------------------------------------------------
-- QUERY 2: Critical Casualty Triage & ICU Bed Availability
-- Shows hospitals with verified ICU capacity for emergency routing
-- ----------------------------------------------------------------------------
SELECT 
    HOSPITAL_ID,
    HOSPITAL_NAME,
    CITY,
    AVAILABLE_ICU_BEDS,
    TOTAL_ICU_BEDS,
    VENTILATORS_ACTIVE,
    BLOOD_UNITS_ONEG,
    STATUS
FROM SANJEEVNI_HOSPITALS
WHERE AVAILABLE_ICU_BEDS > 0
ORDER BY AVAILABLE_ICU_BEDS DESC;


-- ----------------------------------------------------------------------------
-- QUERY 3: ACID Concurrency Check (Atomic ICU Bed Reservation)
-- Simulates ambulance reserving an ICU bed before casualty arrival
-- Row-level locking prevents two ambulances from claiming the same last bed
-- ----------------------------------------------------------------------------
UPDATE SANJEEVNI_HOSPITALS
SET AVAILABLE_ICU_BEDS = AVAILABLE_ICU_BEDS - 1,
    LAST_UPDATED = CURRENT TIMESTAMP
WHERE HOSPITAL_ID = 101 AND AVAILABLE_ICU_BEDS > 0;


-- ----------------------------------------------------------------------------
-- QUERY 4: Active Hazard Blockages on Transportation Corridors
-- Queried by A* detour router to avoid flooded underpasses & bridges
-- ----------------------------------------------------------------------------
SELECT 
    HAZARD_ID,
    HAZARD_TITLE,
    HAZARD_TYPE,
    SEVERITY,
    CITY_CORRIDOR,
    LATITUDE,
    LONGITUDE,
    VERIFIED_SOURCE
FROM SANJEEVNI_HAZARDS
WHERE STATUS = 'Active'
ORDER BY REPORTED_AT DESC;


-- ----------------------------------------------------------------------------
-- QUERY 5: AI Multi-Hazard Risk Forecast Summary
-- Synced from Sanjeevni-DisasterNet v3.2 prediction model
-- ----------------------------------------------------------------------------
SELECT 
    HOTSPOT_ID,
    HOTSPOT_NAME,
    HAZARD_TYPE,
    PROBABILITY_PCT,
    SEVERITY,
    TIME_WINDOW,
    STAGING_HOSPITAL
FROM SANJEEVNI_HOTSPOTS
ORDER BY PROBABILITY_PCT DESC;
