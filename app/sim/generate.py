import os
import sys
import random
import datetime

# Configure UTF-8 output for Windows terminal support
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure app module can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import hashlib
from app.core.database import Base, engine, SessionLocal
from app.core.schema import District, PHC, PHCDetail, Medicine, Inventory, DispensingLog, TransferRequest, User

ESSENTIAL_MEDICINES = [
    {
        "id": "MED-AMOX-500",
        "name": "Amoxicillin 500mg",
        "category": "Antibiotic",
        "unit": "strip",
        "barcode_unit": "QR_STRIP_AMOX_500",
        "barcode_box": "QR_BOX_AMOX_500",
        "barcode_carton": "QR_CARTON_AMOX_500"
    },
    {
        "id": "MED-PARA-650",
        "name": "Paracetamol 650mg",
        "category": "Antipyretic",
        "unit": "strip",
        "barcode_unit": "QR_STRIP_PARA_650",
        "barcode_box": "QR_BOX_PARA_650",
        "barcode_carton": "QR_CARTON_PARA_650"
    },
    {
        "id": "MED-ORS-75",
        "name": "ORS Hydration Sachet 21g",
        "category": "Rehydration",
        "unit": "sachet",
        "barcode_unit": "QR_STRIP_ORS_75",
        "barcode_box": "QR_BOX_ORS_75",
        "barcode_carton": "QR_CARTON_ORS_75"
    },
    {
        "id": "MED-INSU-100",
        "name": "Human Insulin 100IU/ml",
        "category": "Diabetes",
        "unit": "vial",
        "barcode_unit": "QR_STRIP_INSU_100",
        "barcode_box": "QR_BOX_INSU_100",
        "barcode_carton": "QR_CARTON_INSU_100"
    },
    {
        "id": "MED-MAL-20",
        "name": "Artemether + Lumefantrine",
        "category": "Antimalarial",
        "unit": "strip",
        "barcode_unit": "QR_STRIP_MAL_20",
        "barcode_box": "QR_BOX_MAL_20",
        "barcode_carton": "QR_CARTON_MAL_20"
    },
    {
        "id": "MED-OXY-10",
        "name": "Oxytocin Injection 10IU",
        "category": "Maternal Emergency",
        "unit": "ampoule",
        "barcode_unit": "QR_STRIP_OXY_10",
        "barcode_box": "QR_BOX_OXY_10",
        "barcode_carton": "QR_CARTON_OXY_10"
    }
]

DISTRICTS_DATA = [
    {"id": "DIS-01", "name": "Nalgonda", "state": "Telangana", "center_lat": 17.0500, "center_lon": 79.2667},
    {"id": "DIS-02", "name": "Khammam", "state": "Telangana", "center_lat": 17.2473, "center_lon": 80.1514},
    {"id": "DIS-03", "name": "Mahabubnagar", "state": "Telangana", "center_lat": 16.7488, "center_lon": 78.0035},
    {"id": "DIS-04", "name": "Karimnagar", "state": "Telangana", "center_lat": 18.4386, "center_lon": 79.1288},
    {"id": "DIS-05", "name": "Warangal", "state": "Telangana", "center_lat": 17.9689, "center_lon": 79.5941}
]

def seed_database():
    print("🔄 Initializing Database Schema (Dropping & Re-creating Tables)...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Seed Medicines
        print("💊 Seeding Essential Medicines Master Data...")
        for med_data in ESSENTIAL_MEDICINES:
            med = Medicine(**med_data)
            db.add(med)
        db.commit()

        # 2. Seed Districts, PHCs & PHC Details
        print("🏥 Seeding Districts, PHCs, and PHC Details Capacity Data...")
        all_phcs = []
        for dis_data in DISTRICTS_DATA:
            dis = District(id=dis_data["id"], name=dis_data["name"], state=dis_data["state"])
            db.add(dis)

            for i in range(1, 5):
                phc_id = f"PHC-D{dis_data['id'][-2:]}-{i:02d}"
                lat = dis_data["center_lat"] + random.uniform(-0.15, 0.15)
                lon = dis_data["center_lon"] + random.uniform(-0.15, 0.15)
                phc_name = f"{dis_data['name']} Area PHC #{i}"
                
                phc = PHC(
                    id=phc_id,
                    name=phc_name,
                    district_id=dis_data["id"],
                    mandal_name=f"{dis_data['name']} Mandal #{i}",
                    pincode=f"508{i:03d}",
                    latitude=round(lat, 4),
                    longitude=round(lon, 4)
                )
                db.add(phc)

                # Add PHCDetail
                detail = PHCDetail(
                    phc_id=phc_id,
                    facility_type=random.choice(["Rural", "Rural", "Urban", "Tribal"]),
                    bed_capacity=random.choice([6, 8, 10, 20]),
                    avg_daily_op=random.randint(40, 120),
                    emergency_24x7=random.choice([True, False]),
                    cold_chain_available=True
                )
                db.add(detail)
                all_phcs.append(phc_id)
        db.commit()

        # 3. Seed Inventory & Historical Dispensing Logs (60 Days)
        print("📊 Generating 60-day historical dispensing logs & inventory balances...")
        now = datetime.datetime.utcnow()
        batch_counter = 100

        for phc_id in all_phcs:
            for med in ESSENTIAL_MEDICINES:
                med_id = med["id"]
                avg_daily = float(random.randint(25, 120))
                safety_threshold = int(avg_daily * 7)

                if phc_id == "PHC-D01-03" and med_id == "MED-PARA-650":
                    initial_stock = 50
                    avg_daily = 50.0
                elif phc_id == "PHC-D01-01" and med_id == "MED-PARA-650":
                    initial_stock = 4500
                    avg_daily = 50.0
                else:
                    initial_stock = int(avg_daily * random.randint(15, 45))

                batch_num = f"BAT-2026-X{batch_counter}"
                batch_counter += 1
                exp_date = (now + datetime.timedelta(days=random.randint(120, 500))).strftime("%Y-%m-%d")

                inv = Inventory(
                    phc_id=phc_id,
                    medicine_id=med_id,
                    current_stock=initial_stock,
                    safety_threshold=safety_threshold,
                    avg_daily_consumption=avg_daily,
                    batch_number=batch_num,
                    expiry_date=exp_date,
                    last_updated=now
                )
                db.add(inv)

                for day_offset in range(60, 0, -1):
                    log_date = now - datetime.timedelta(days=day_offset)
                    daily_quantity = max(1, int(avg_daily * random.uniform(0.75, 1.25)))
                    log = DispensingLog(
                        phc_id=phc_id,
                        medicine_id=med_id,
                        quantity=daily_quantity,
                        ingestion_mode=random.choice(["camera_scan", "camera_scan", "camera_scan", "manual_entry"]),
                        timestamp=log_date
                    )
                    db.add(log)

        db.commit()

        # 4. Sample Transfer Request
        sample_tr = TransferRequest(
            id="TR-2026-001",
            source_phc_id="PHC-D01-01",
            target_phc_id="PHC-D01-03",
            medicine_id="MED-PARA-650",
            quantity=800,
            distance_km=18.5,
            status="proposed",
            reason="Automated Redistribution: PHC-D01-03 Paracetamol risk forecast critical (< 2 days)."
        )
        db.add(sample_tr)
        db.commit()

        # 5. Default Demo Users
        def _hp(p): return hashlib.sha256(p.encode('utf-8')).hexdigest()
        admin_user = User(
            id="USR-ADMIN-01",
            username="admin",
            email="admin@resilience.gov.in",
            password_hash=_hp("admin123"),
            full_name="District Officer (Admin)",
            role="district_admin",
            status="active",
            last_login=now
        )
        staff_user = User(
            id="USR-STAFF-01",
            username="staff_loddaputti",
            email="staff@loddaputti.phc",
            password_hash=_hp("staff123"),
            full_name="Nurse Practitioner (Loddaputti)",
            role="phc_staff",
            phc_id="PHC-D01-03",
            status="active",
            last_login=now
        )
        db.add(admin_user)
        db.add(staff_user)
        db.commit()

        print("✅ Database seeding complete! Successfully generated:")
        print(f"   • 5 Districts")
        print(f"   • 20 Core PHCs")
        print(f"   • 20 PHC Detail Capability Records")
        print(f"   • 6 Essential Medicines")
        print(f"   • 120 Inventory Records")
        print(f"   • 7,200 Historical Dispensing Logs")
        print(f"   • 1 Sample Transfer Request")
        print(f"   • 2 Initial Demo Accounts (admin / staff_loddaputti)")

    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
