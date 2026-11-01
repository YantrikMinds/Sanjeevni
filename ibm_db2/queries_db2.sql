-- =====================================================================
-- SANJEEVNI: IBM Db2 Tactical Analysis & Mission Queries
-- Open and Execute in VS Code using 'IBM Db2 Developer Extension'
-- =====================================================================

-- ---------------------------------------------------------------------
-- QUERY 1: TACTICAL LIFE-CRITICAL SURVIVORS REQUIRING RESCUE DISPATCH
-- Returns trapped individuals detected by Edge Vision waiting for USAR Squad
-- ---------------------------------------------------------------------
SELECT 
    S.DETECTION_ID,
    S.DETECTION_CLASS,
    S.CONFIDENCE_PCT AS "CONFIDENCE (%)",
    F.DEVICE_NAME AS "DETECTED BY ROVER",
    SEC.SECTOR_NAME,
    SEC.COLLAPSE_TYPE,
    S.DETECTED_LAT,
    S.DETECTED_LNG,
    S.STATUS,
    S.DETECTION_TIMESTAMP
FROM SANJEEVNI_SURVIVORS S
JOIN SANJEEVNI_FLEET F ON S.DETECTED_BY_NODE = F.NODE_ID
JOIN SANJEEVNI_SECTORS SEC ON S.SECTOR_CODE = SEC.SECTOR_CODE
WHERE S.STATUS = 'AWAITING_DISPATCH'
ORDER BY S.CONFIDENCE_PCT DESC;


-- ---------------------------------------------------------------------
-- QUERY 2: ROVER FLEET TELEMETRY & STRUCTURAL HAZARD MONITOR
-- Checks if any rover is in danger (Hazard Tilt > 25° or Toxic CH4 > 50 PPM)
-- ---------------------------------------------------------------------
SELECT 
    NODE_ID,
    DEVICE_NAME,
    STATUS,
    BATTERY_PCT AS "BATTERY (%)",
    IMU_TILT_DEG AS "STRUCTURAL TILT (°)",
    CASE 
        WHEN IMU_TILT_DEG > 25.0 THEN '⚠️ HAZARD: AFTERSHOCK SHIFT'
        ELSE 'STABLE'
    END AS "STRUCTURAL STATE",
    CH4_METHANE_PPM AS "METHANE (PPM)",
    CASE 
        WHEN CH4_METHANE_PPM > 50.0 THEN '🚨 EXPLOSIVE / TOXIC'
        ELSE 'SAFE'
    END AS "ATMOSPHERE STATE",
    VOID_CLEARANCE_M AS "VOID CLEARANCE (m)",
    ASSIGNED_SECTOR
FROM SANJEEVNI_FLEET
ORDER BY BATTERY_PCT DESC;


-- ---------------------------------------------------------------------
-- QUERY 3: SECTOR TRIAGE RANKING (DISASTER SEVERITY MATRIX)
-- Combines estimated victims, collapse physics, and safe corridor clearance
-- ---------------------------------------------------------------------
SELECT 
    SECTOR_CODE,
    SECTOR_NAME,
    COLLAPSE_TYPE,
    HAZARD_LEVEL,
    ESTIMATED_VICTIMS,
    CLEARANCE_CORRIDOR_SAFE,
    COALESCE(ASSIGNED_NODE, 'UNASSIGNED') AS "SCOUT ROVER",
    COUNT(S.DETECTION_ID) AS "VERIFIED SURVIVORS DETECTED"
FROM SANJEEVNI_SECTORS SEC
LEFT JOIN SANJEEVNI_SURVIVORS S ON SEC.SECTOR_CODE = S.SECTOR_CODE
GROUP BY SECTOR_CODE, SECTOR_NAME, COLLAPSE_TYPE, HAZARD_LEVEL, ESTIMATED_VICTIMS, CLEARANCE_CORRIDOR_SAFE, ASSIGNED_NODE
ORDER BY 
    CASE HAZARD_LEVEL
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MODERATE' THEN 3
        ELSE 4
    END;


-- ---------------------------------------------------------------------
-- QUERY 4: UN INSARAG DISPATCH AUDIT TRAIL
-- Cryptographically verified commander authorizations for hospital routing
-- ---------------------------------------------------------------------
SELECT 
    D.DISPATCH_ID,
    D.COMMANDER_NAME,
    D.ACTION_TAKEN,
    D.SIGN_OFF_HASH,
    D.DISPATCH_TIMESTAMP,
    D.HOSPITAL_DESTINATION,
    S.SECTOR_CODE,
    S.CONFIDENCE_PCT
FROM SANJEEVNI_DISPATCH_LOG D
JOIN SANJEEVNI_SURVIVORS S ON D.DETECTION_ID = S.DETECTION_ID
ORDER BY D.DISPATCH_TIMESTAMP DESC;
