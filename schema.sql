-- ============================================================
-- Project Resilience: MySQL Database Schema Creation Script
-- Database: resilience_db
-- ============================================================

CREATE DATABASE IF NOT EXISTS resilience_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE resilience_db;

-- 1. Districts Table
CREATE TABLE IF NOT EXISTS districts (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL DEFAULT 'Andhra Pradesh'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Core Primary Health Centres (PHCs) Table
CREATE TABLE IF NOT EXISTS phcs (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    district_id VARCHAR(50) NOT NULL,
    mandal_name VARCHAR(100),
    pincode VARCHAR(20),
    latitude DOUBLE,
    longitude DOUBLE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Extended PHC Details / Capacity Table
CREATE TABLE IF NOT EXISTS phc_details (
    phc_id VARCHAR(50) PRIMARY KEY,
    facility_type VARCHAR(50) DEFAULT 'Rural', -- Rural | Urban | Tribal
    bed_capacity INT DEFAULT 6,
    avg_daily_op INT DEFAULT 50,              -- Average Daily Outpatients
    emergency_24x7 BOOLEAN DEFAULT FALSE,
    cold_chain_available BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (phc_id) REFERENCES phcs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Essential Medicines Table
CREATE TABLE IF NOT EXISTS medicines (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    category VARCHAR(100) NOT NULL,
    unit VARCHAR(50) DEFAULT 'strip',
    barcode_unit VARCHAR(100) UNIQUE,
    barcode_box VARCHAR(100) UNIQUE,
    barcode_carton VARCHAR(100) UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Inventory Balances Table
CREATE TABLE IF NOT EXISTS inventory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    phc_id VARCHAR(50) NOT NULL,
    medicine_id VARCHAR(50) NOT NULL,
    current_stock INT NOT NULL DEFAULT 0,
    safety_threshold INT NOT NULL DEFAULT 200,
    avg_daily_consumption DOUBLE NOT NULL DEFAULT 50.0,
    batch_number VARCHAR(100),
    expiry_date VARCHAR(20),
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (phc_id) REFERENCES phcs(id) ON DELETE CASCADE,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE,
    UNIQUE KEY uq_phc_medicine (phc_id, medicine_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Dispensing Transaction Logs Table
CREATE TABLE IF NOT EXISTS dispensing_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    phc_id VARCHAR(50) NOT NULL,
    medicine_id VARCHAR(50) NOT NULL,
    quantity INT NOT NULL,
    ingestion_mode VARCHAR(50) DEFAULT 'camera_scan', -- camera_scan | manual_entry | bulk_qr
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (phc_id) REFERENCES phcs(id) ON DELETE CASCADE,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Stock Transfer & Redistribution Requests Table
CREATE TABLE IF NOT EXISTS transfers (
    id VARCHAR(50) PRIMARY KEY,
    source_phc_id VARCHAR(50) NOT NULL,
    target_phc_id VARCHAR(50) NOT NULL,
    medicine_id VARCHAR(50) NOT NULL,
    quantity INT NOT NULL,
    distance_km DOUBLE DEFAULT 15.0,
    status VARCHAR(50) DEFAULT 'proposed', -- proposed | approved | in_transit | completed | rejected
    reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_phc_id) REFERENCES phcs(id) ON DELETE CASCADE,
    FOREIGN KEY (target_phc_id) REFERENCES phcs(id) ON DELETE CASCADE,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
