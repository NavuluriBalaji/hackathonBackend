# 🎬 Project Resilience — Official Hackathon Demo Script & Testing Walkthrough

> **System Overview**: Project Resilience is a Sovereign Federated Learning & AI-Powered Health Supply Chain System designed for Primary Health Centers (PHCs) and District Medical Officers (DMOs) to eliminate critical medicine stockouts across India & BRICS nations.
>
> **Live API Base URL**: `https://project-resilience-api-255126562814.us-central1.run.app`  
> **Interactive Swagger Docs**: `https://project-resilience-api-255126562814.us-central1.run.app/docs`

---

## 🔑 Pre-Configured Demo Credentials

| Role | Username / Identifier | Password | Primary Actions / Scope |
| :--- | :--- | :--- | :--- |
| **District Admin (DMO)** | `admin` | `admin123` | Multi-district map, stockout alerts, AI redistribution, federated learning |
| **PHC Staff Nurse** | `staff_loddaputti` | `staff123` | Local inventory ledger, camera/barcode dispensing, bed capacity sync |
| **Cold-Chain Driver** | `DRV-DIS-01-01` | N/A | Driver dispatch, pickup verification, OTP delivery confirmation |

---

## 🎥 Video Recording Flow & Scene Breakdown (3-Minute Script)

### Scene 1: The Problem & DMO Command Center (0:00 - 0:45)
* **Visual**: Open frontend / Swagger docs or Postman targeting `https://project-resilience-api-255126562814.us-central1.run.app/docs`.
* **Voiceover Narrative**: 
  > *"In rural primary health centers across developing nations, stockouts of essential life-saving medicines like Insulin, Paracetamol, and Oxytocin cost lives. Today, we introduce Project Resilience—a sovereign, AI-driven health supply chain system that predicts stockouts before they happen and automates peer-to-peer redistribution across 73 PHCs."*
* **API Action**:
  - `GET /api/districts` $\rightarrow$ Demonstrates **33 Districts** loaded.
  - `GET /api/phcs` $\rightarrow$ Demonstrates **73 PHCs** with real-time status color coding (🟢 Safe, 🟡 Warning, 🔴 Critical).

---

### Scene 2: Real-Time Emergency Outbreak & AI Prediction (0:45 - 1:30)
* **Visual**: Highlight a PHC experiencing stock depletion (e.g. `PHC-D01-03` / PHC Loddaputti).
* **Voiceover Narrative**: 
  > *"Our machine learning model analyzes 60 days of historical dispensing logs to forecast stockout risk. Here, PHC Loddaputti has less than 2 days of Paracetamol remaining due to a seasonal surge."*
* **API Action**:
  - `GET /api/phcs/PHC-D01-03/inventory-ledger` $\rightarrow$ Displays low stock balance & risk level `CRITICAL`.
  - `POST /api/optimizer/predict-stockouts` $\rightarrow$ Runs forecasting algorithm to identify donor PHCs (e.g., `PHC-D01-01` with 15 days cover).

---

### Scene 3: Automated Peer-to-Peer Redistribution & Cold-Chain Fleet (1:30 - 2:15)
* **Visual**: Create an emergency transfer request from Donor PHC to Recipient PHC.
* **Voiceover Narrative**: 
  > *"Instead of waiting weeks for central warehouse supply, Project Resilience calculates real-time road distances and dispatches the nearest available Cold-Chain Van driver to transfer surplus stock from a neighboring PHC within 25 minutes."*
* **API Action**:
  - `POST /api/transfers/propose` $\rightarrow$ Generates Transfer Request `TR-2026-001`.
  - `GET /api/drivers` $\rightarrow$ Fetches nearby drivers (`DRV-DIS-01-01` Ramesh Kumar).
  - `POST /api/transfers/assign-driver` $\rightarrow$ Assigns driver & generates 4-digit Handover OTP.

---

### Scene 4: Mobile Dispensing & OTP Handover Verification (2:15 - 2:45)
* **Visual**: Staff nurse dispenses medicine and driver verifies delivery via OTP.
* **Voiceover Narrative**: 
  > *"At the PHC, staff scan medicine barcodes to log daily dispensing, instantly updating inventory balances. Upon arrival, the cold-chain driver enters the recipient's OTP to verify tamper-proof handover."*
* **API Action**:
  - `POST /api/phcs/PHC-D01-03/dispense` $\rightarrow$ Deducts stock in real-time.
  - `POST /api/transfers/verify-delivery` $\rightarrow$ Verifies OTP code and updates transfer status to `completed`.

---

### Scene 5: Sovereign Federated Learning & Conclusion (2:45 - 3:00)
* **Visual**: Trigger Federated Learning round.
* **Voiceover Narrative**: 
  > *"Finally, to preserve patient privacy and data sovereignty, model training occurs locally at each PHC. Only encrypted model weights are aggregated globally. Project Resilience guarantees health supply chain sovereignty for the future."*
* **API Action**:
  - `POST /api/federated/train-round` $\rightarrow$ Executes FL aggregation round.

---

## 🛠️ Step-by-Step API Testing Pathway (cURL Commands)

### 1. Verify System Health & Core Directory
```bash
# Health Check
curl -s https://project-resilience-api-255126562814.us-central1.run.app/health

# Fetch All 73 PHCs with Capacity & Staffing
curl -s https://project-resilience-api-255126562814.us-central1.run.app/api/phcs

# Fetch All 33 Districts
curl -s https://project-resilience-api-255126562814.us-central1.run.app/api/districts
```

### 2. User Authentication (Signup & Login)
```bash
# Login as District Admin
curl -X POST https://project-resilience-api-255126562814.us-central1.run.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username_or_email": "admin", "password": "admin123"}'

# Register a New PHC Staff User
curl -X POST https://project-resilience-api-255126562814.us-central1.run.app/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "nurse_visakha",
    "email": "nurse@visakha.phc",
    "password": "Password123!",
    "full_name": "Nurse Anitha",
    "role": "phc_staff",
    "phc_identifier": "PHC-AP02-01"
  }'
```

### 3. Inventory Ledger & Dispensing
```bash
# View Inventory Ledger for PHC-D01-03
curl -s https://project-resilience-api-255126562814.us-central1.run.app/api/phcs/PHC-D01-03/inventory-ledger

# Dispense 50 units of Paracetamol (MED-PARA-650)
curl -X POST https://project-resilience-api-255126562814.us-central1.run.app/api/phcs/PHC-D01-03/dispense \
  -H "Content-Type: application/json" \
  -d '{
    "medicine_id": "MED-PARA-650",
    "quantity": 50,
    "ingestion_mode": "camera_scan"
  }'
```

### 4. Cold-Chain Fleet & Transfer Handover
```bash
# View Available Cold-Chain Drivers
curl -s https://project-resilience-api-255126562814.us-central1.run.app/api/drivers

# Complete Delivery Verification with OTP
curl -X POST https://project-resilience-api-255126562814.us-central1.run.app/api/transfers/verify-delivery \
  -H "Content-Type: application/json" \
  -d '{
    "transfer_id": "TR-2026-001",
    "otp_code": "4821"
  }'
```

---

## 🏆 Key Presentation Points for Judges

1. **Production-Grade Infrastructure**: Hosted on **Google Cloud Run** connected to **Cloud Render PostgreSQL** with SSL connection pooling and < 1.0s endpoint response time.
2. **Complete Data Persistence**: Fully populated with **73 PHCs**, **33 Districts**, **7,200 Dispensing Logs**, and **Cold-Chain Drivers**.
3. **Data Sovereignty**: Built-in **Federated Learning** server keeping patient dispensing logs localized while improving global demand forecasting models.
