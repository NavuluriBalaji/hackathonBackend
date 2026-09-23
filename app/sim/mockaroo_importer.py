import os
import sys
import argparse
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session

# Configure UTF-8 output for Windows terminal
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import SessionLocal
from app.core.schema import PHC, PHCDetail, Medicine, Inventory, DispensingLog, Driver, District, TransferRequest

def import_districts(df: pd.DataFrame, db: Session):
    count = 0
    updated = 0
    for idx, row in df.iterrows():
        dis_id = str(row.get("id") if pd.notnull(row.get("id")) else f"DIS-AP-{idx+1:02d}").strip()
        name = str(row.get("name", f"District #{idx+1}")).strip()
        state = str(row.get("state", "Andhra Pradesh")).strip()

        existing = db.query(District).filter(District.id == dis_id).first()
        if not existing:
            existing = db.query(District).filter(District.name == name).first()

        if existing:
            existing.name = name
            existing.state = state
            updated += 1
        else:
            dis = District(id=dis_id, name=name, state=state)
            db.add(dis)
            count += 1

    db.commit()
    print(f"✅ Created {count} new district records and updated {updated} existing district records!")

def import_dispensing_logs(df: pd.DataFrame, db: Session):
    count = 0
    for idx, row in df.iterrows():
        phc_id = str(row.get("phc_id", "PHC-AP-01")).strip()
        med_id = str(row.get("medicine_id", "MED-AMOX-500")).strip()
        qty = int(row.get("quantity", 10))
        mode = str(row.get("ingestion_mode", "camera_scan")).strip()
        
        raw_ts = row.get("timestamp")
        ts = datetime.utcnow()
        if pd.notnull(raw_ts):
            try:
                ts = pd.to_datetime(raw_ts).to_pydatetime()
            except Exception:
                pass

        phc = db.query(PHC).filter(PHC.id == phc_id).first()
        med = db.query(Medicine).filter(Medicine.id == med_id).first()

        if phc and med:
            log = DispensingLog(
                phc_id=phc_id,
                medicine_id=med_id,
                quantity=qty,
                ingestion_mode=mode,
                timestamp=ts
            )
            db.add(log)
            count += 1

    db.commit()
    print(f"✅ Added {count} new Dispensing Log records!")

def import_inventory(df: pd.DataFrame, db: Session):
    count = 0
    updated = 0
    for idx, row in df.iterrows():
        phc_id = str(row.get("phc_id", "PHC-AP-01")).strip()
        med_id = str(row.get("medicine_id", "MED-AMOX-500")).strip()
        stock = int(row.get("current_stock", 500))
        threshold = int(row.get("safety_threshold", 200))
        avg_daily = float(row.get("avg_daily_consumption", 25.0))
        batch = str(row.get("batch_number", "BAT-2026-001")).strip()
        expiry = str(row.get("expiry_date", "2027-12-31")).strip()

        phc = db.query(PHC).filter(PHC.id == phc_id).first()
        med = db.query(Medicine).filter(Medicine.id == med_id).first()

        if phc and med:
            existing = db.query(Inventory).filter(
                Inventory.phc_id == phc_id,
                Inventory.medicine_id == med_id
            ).first()

            if existing:
                existing.current_stock = stock
                existing.safety_threshold = threshold
                existing.avg_daily_consumption = avg_daily
                existing.batch_number = batch
                existing.expiry_date = expiry
                existing.last_updated = datetime.utcnow()
                updated += 1
            else:
                inv = Inventory(
                    phc_id=phc_id,
                    medicine_id=med_id,
                    current_stock=stock,
                    safety_threshold=threshold,
                    avg_daily_consumption=avg_daily,
                    batch_number=batch,
                    expiry_date=expiry,
                    last_updated=datetime.utcnow()
                )
                db.add(inv)
                count += 1

    db.commit()
    print(f"✅ Created {count} new inventory records and updated {updated} existing inventory records!")

def import_drivers(df: pd.DataFrame, db: Session):
    count = 0
    updated = 0
    for idx, row in df.iterrows():
        drv_id = str(row.get("id", f"DRV-MOCK-{idx+1:03d}")).strip()
        name = str(row.get("name", "Driver")).strip()
        phone = str(row.get("phone", "+91 98480 00000")).strip()
        v_type = str(row.get("vehicle_type", "Cold-Chain Van")).strip()
        v_num = str(row.get("vehicle_number", f"TS-03-E-{1000+idx}")).strip()
        dis_id = str(row.get("district_id", "DIS-01")).strip()
        status = str(row.get("status", "available")).strip()
        lat = float(row.get("current_lat", 17.0500))
        lon = float(row.get("current_lon", 79.2667))

        existing = db.query(Driver).filter(Driver.id == drv_id).first()
        if existing:
            existing.name = name
            existing.phone = phone
            existing.vehicle_type = v_type
            existing.vehicle_number = v_num
            existing.status = status
            existing.current_lat = lat
            existing.current_lon = lon
            updated += 1
        else:
            drv = Driver(
                id=drv_id,
                name=name,
                phone=phone,
                vehicle_type=v_type,
                vehicle_number=v_num,
                district_id=dis_id,
                status=status,
                current_lat=lat,
                current_lon=lon
            )
            db.add(drv)
            count += 1

    db.commit()
    print(f"✅ Created {count} new drivers and updated {updated} existing driver records!")

def import_medicines(df: pd.DataFrame, db: Session):
    import random
    count = 0
    updated = 0
    for idx, row in df.iterrows():
        med_id = str(row.get("id") if pd.notnull(row.get("id")) else row.get("medicine_id", "")).strip()
        if not med_id or "#{" in med_id or "{{" in med_id or "pad" in med_id or "digit" in med_id or "row_num" in med_id or "CUSTOM-#" in med_id or med_id == "nan":
            med_id = f"MED-CUSTOM-{idx+1:03d}"

        name = str(row.get("name", "Medicine Name")).strip().replace("\n", " ")[:145]
        cat = str(row.get("category", "General")).strip()[:95]
        brand = str(row.get("brand_name", "")).strip()[:145]
        generic = str(row.get("generic_name", "")).strip()[:145]
        unit = str(row.get("unit", "strip")).strip()[:45]

        bc_u = str(row.get("barcode_unit", "")).strip()
        bc_b = str(row.get("barcode_box", "")).strip()
        bc_c = str(row.get("barcode_carton", "")).strip()

        rnd_num = random.randint(10000, 99999)
        med_clean = med_id.replace("MED-", "").replace("-", "_")

        if not bc_u or "#{" in bc_u or "{{" in bc_u or "random" in bc_u or "digit" in bc_u:
            bc_u = f"QR_STRIP_{med_clean}_{idx+1:04d}_{rnd_num}"
        if not bc_b or "#{" in bc_b or "{{" in bc_b or "random" in bc_b or "digit" in bc_b:
            bc_b = f"QR_BOX_{med_clean}_{idx+1:04d}_{rnd_num}"
        if not bc_c or "#{" in bc_c or "{{" in bc_c or "random" in bc_c or "digit" in bc_c:
            bc_c = f"QR_CARTON_{med_clean}_{idx+1:04d}_{rnd_num}"

        existing = db.query(Medicine).filter(Medicine.id == med_id).first()
        if existing:
            existing.name = name
            existing.category = cat
            existing.brand_name = brand
            existing.generic_name = generic
            existing.unit = unit
            updated += 1
        else:
            med = Medicine(
                id=med_id,
                name=name,
                category=cat,
                brand_name=brand,
                generic_name=generic,
                unit=unit,
                barcode_unit=bc_u,
                barcode_box=bc_b,
                barcode_carton=bc_c
            )
            db.add(med)
            count += 1

    db.commit()
    print(f"✅ Created {count} new medicine records and updated {updated} existing medicine records!")

def import_phcs(df: pd.DataFrame, db: Session):
    import random
    count = 0
    updated = 0
    detail_count = 0
    for idx, row in df.iterrows():
        phc_id = str(row.get("id") if pd.notnull(row.get("id")) else f"PHC-MOCK-{idx+1:03d}").strip()
        name = str(row.get("name", f"PHC #{idx+1}")).strip()
        dis_id = str(row.get("district_id", "DIS-AP-01")).strip()
        mandal = str(row.get("mandal_name") if pd.notnull(row.get("mandal_name")) else row.get("mandal", "Mandal")).strip()
        pincode = str(row.get("pincode", "530001")).strip()
        lat = float(row.get("latitude") if pd.notnull(row.get("latitude")) else row.get("lat", 17.5000))
        lon = float(row.get("longitude") if pd.notnull(row.get("longitude")) else row.get("lon", 82.5000))

        facility_type = str(row.get("facility_type") if pd.notnull(row.get("facility_type")) else row.get("type", "Rural")).strip()
        beds = int(row.get("bed_capacity") if pd.notnull(row.get("bed_capacity")) else row.get("beds", 10))
        op = int(row.get("avg_daily_op") if pd.notnull(row.get("avg_daily_op")) else row.get("op", 60))

        dis = db.query(District).filter(District.id == dis_id).first()
        if not dis:
            # try finding district by name or default to first
            dis = db.query(District).first()
            if dis:
                dis_id = dis.id

        existing = db.query(PHC).filter(PHC.id == phc_id).first()
        if existing:
            existing.name = name
            existing.district_id = dis_id
            existing.mandal_name = mandal
            existing.pincode = pincode
            existing.latitude = lat
            existing.longitude = lon
            updated += 1
        else:
            phc = PHC(
                id=phc_id,
                name=name,
                district_id=dis_id,
                mandal_name=mandal,
                pincode=pincode,
                latitude=lat,
                longitude=lon
            )
            db.add(phc)
            count += 1

        existing_detail = db.query(PHCDetail).filter(PHCDetail.phc_id == phc_id).first()
        if not existing_detail:
            detail = PHCDetail(
                phc_id=phc_id,
                facility_type=facility_type,
                bed_capacity=beds,
                occupied_beds=random.randint(2, max(3, beds)),
                avg_daily_op=op,
                emergency_24x7=random.choice([True, False]),
                cold_chain_available=True,
                doctors_assigned=random.randint(2, 4),
                doctors_present=random.randint(2, 4),
                nurses_assigned=random.randint(4, 8),
                nurses_present=random.randint(4, 8),
                last_attendance_sync=datetime.utcnow()
            )
            db.add(detail)
            detail_count += 1

    db.commit()
    print(f"✅ Created {count} new PHC records, updated {updated} existing PHC records, and created {detail_count} PHC Details!")

def main():
    parser = argparse.ArgumentParser(description="Import Mockaroo CSV into MySQL Database")
    parser.add_argument("--type", required=True, choices=["dispensing_logs", "inventory", "drivers", "medicines", "districts", "phcs"], help="Type of data to import")
    parser.add_argument("--file", required=True, help="Path to Mockaroo CSV file")
    
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"❌ File not found: {args.file}")
        sys.exit(1)

    print(f"📥 Loading CSV file: {args.file} for table type: '{args.type}'")
    df = pd.read_csv(args.file)
    db = SessionLocal()

    try:
        if args.type == "dispensing_logs":
            import_dispensing_logs(df, db)
        elif args.type == "inventory":
            import_inventory(df, db)
        elif args.type == "drivers":
            import_drivers(df, db)
        elif args.type == "medicines":
            import_medicines(df, db)
        elif args.type == "districts":
            import_districts(df, db)
        elif args.type == "phcs":
            import_phcs(df, db)
    except Exception as e:
        print(f"❌ Error importing Mockaroo dataset: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()

