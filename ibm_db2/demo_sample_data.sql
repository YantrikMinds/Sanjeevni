-- =====================================================================
-- SANJEEVNI: IBM Db2 Sample Disaster Data
-- Demonstrates Live Tactical Sync from Moto G62 & iPhone 13 Rovers
-- =====================================================================

-- 1. Insert Active Rover Fleet
INSERT INTO SANJEEVNI_FLEET (NODE_ID, DEVICE_NAME, MODEL, STATUS, BATTERY_PCT, MESH_RSSI_DBM, IMU_TILT_DEG, CH4_METHANE_PPM, CO_PPM, VOID_CLEARANCE_M, ASSIGNED_SECTOR)
VALUES 
('MOTO-G62', 'Rover Alpha (Moto G62)', 'Motorola Moto G62 5G', 'ACTIVE', 92, -64, 5.2, 16.5, 7.2, 1.15, 'SEC-B2'),
('IPHONE-13', 'Rover Beta (iPhone 13)', 'Apple iPhone 13', 'ACTIVE', 89, -60, 4.1, 14.8, 6.5, 1.22, 'SEC-D4'),
('ROVER-03', 'Rover Gamma (Unit 03)', 'Samsung S21 Rugged', 'STANDBY', 96, -72, 0.0, 11.2, 4.0, 1.50, 'SEC-A1');

-- 2. Insert Sectors
INSERT INTO SANJEEVNI_SECTORS (SECTOR_CODE, SECTOR_NAME, COLLAPSE_TYPE, HAZARD_LEVEL, LATITUDE, LONGITUDE, ASSIGNED_NODE, ESTIMATED_VICTIMS, CLEARANCE_CORRIDOR_SAFE)
VALUES
('SEC-B2', 'Sector B-2: Grand Palace Hotel Collapse', 'PANCAKE', 'CRITICAL', 28.704100, 77.102500, 'MOTO-G62', 2, 'Y'),
('SEC-D4', 'Sector D-4: Sunrise Apartments (Block C)', 'LEAN_TO', 'HIGH', 28.705800, 77.104200, 'IPHONE-13', 1, 'Y'),
('SEC-A1', 'Sector A-1: Metro Concourse Basement', 'CANTILEVER', 'MODERATE', 28.708200, 77.101100, 'ROVER-03', 0, 'N'),
('SEC-C3', 'Sector C-3: City Hospital South Corridor', 'CLEARED', 'CLEARED', 28.701500, 77.106500, NULL, 0, 'Y');

-- 3. Insert Live Detected Survivors
INSERT INTO SANJEEVNI_SURVIVORS (DETECTED_BY_NODE, SECTOR_CODE, DETECTION_CLASS, CONFIDENCE_PCT, DETECTED_LAT, DETECTED_LNG, STATUS, COMMANDER_SIGNOFF)
VALUES
('MOTO-G62', 'SEC-B2', 'HUMAN LIMB', 88.50, 28.704120, 77.102510, 'DISPATCHED', 'Commander Nishant Pathak'),
('IPHONE-13', 'SEC-D4', 'HUMAN LIMB', 91.20, 28.705840, 77.104230, 'AWAITING_DISPATCH', NULL);

-- 4. Insert Commander Dispatch Audit Log (UN INSARAG Compliance)
INSERT INTO SANJEEVNI_DISPATCH_LOG (DETECTION_ID, COMMANDER_NAME, ACTION_TAKEN, SIGN_OFF_HASH, HOSPITAL_DESTINATION)
VALUES
(1001, 'Commander Nishant Pathak', 'DISPATCH_USAR', '7a4b8f9e12c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9', 'AIIMS Trauma Center South');
