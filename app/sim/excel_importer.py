import os
import sys
import pandas as pd
import datetime

# Configure UTF-8 output for Windows terminal support
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure backend package can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import SessionLocal
from app.core.schema import District, PHC, PHCDetail, Medicine, Inventory

def import_ap_csv_dataset(csv_path: str):
    """Imports real Andhra Pradesh PHC dataset (ap_all_districts_phc_dataset.csv) into MySQL."""
    if not os.path.exists(csv_path):
        print(f"❌ AP CSV file not found: {csv_path}")
        return False

    print(f"📥 Ingesting AP PHC CSV dataset: {csv_path}")
    df = pd.read_csv(csv_path)
    db = SessionLocal()

    dis_count, phc_count, detail_count = 0, 0, 0
    try:
        for idx, row in df.iterrows():
            dis_name = str(row["District"]).strip()
            dis_id = f"DIS-{dis_name.upper().replace(' ', '_').replace('.', '')}"

            # 1. Upsert District
            existing_dis = db.query(District).filter(District.id == dis_id).first()
            if not existing_dis:
                dis = District(id=dis_id, name=dis_name, state="Andhra Pradesh")
                db.add(dis)
                db.commit()
                dis_count += 1

            # 2. Upsert Core PHC Node
            phc_name = str(row["PHC_Name"]).strip()
            phc_id = f"PHC-AP-{idx+1:03d}"
            mandal = str(row["Mandal"]).strip()
            pincode = str(row["Pincode"]).strip()

            existing_phc = db.query(PHC).filter(PHC.id == phc_id).first()
            if not existing_phc:
                phc = PHC(
                    id=phc_id,
                    name=phc_name,
                    district_id=dis_id,
                    mandal_name=mandal,
                    pincode=pincode,
                    latitude=16.5000 + (idx * 0.05) % 2.0, # Approximate coordinates for mapping
                    longitude=80.6000 + (idx * 0.08) % 3.0
                )
                db.add(phc)
                db.commit()
                phc_count += 1

            # 3. Upsert Extended PHC Details / Capacity
            f_type = str(row["Type"]).strip()
            beds = int(row["Bed_Capacity"])
            avg_op = int(row["Avg_Daily_OP"])
            emergency = str(row["Emergency_24x7"]).strip().lower() == "yes"

            existing_detail = db.query(PHCDetail).filter(PHCDetail.phc_id == phc_id).first()
            if not existing_detail:
                detail = PHCDetail(
                    phc_id=phc_id,
                    facility_type=f_type,
                    bed_capacity=beds,
                    avg_daily_op=avg_op,
                    emergency_24x7=emergency,
                    cold_chain_available=True
                )
                db.add(detail)
                detail_count += 1
            else:
                existing_detail.facility_type = f_type
                existing_detail.bed_capacity = beds
                existing_detail.avg_daily_op = avg_op
                existing_detail.emergency_24x7 = emergency

        db.commit()
        print(f"✅ Successfully ingested AP PHC Dataset:")
        print(f"   • {dis_count} new Districts created")
        print(f"   • {phc_count} core PHCs created")
        print(f"   • {detail_count} PHC Details metadata records created")
        return True
    except Exception as e:
        print(f"❌ Error ingesting AP CSV data: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    default_csv = r"d:\dev\personal\Hackathon\ap_all_districts_phc_dataset.csv"
    csv_file = sys.argv[1] if len(sys.argv) > 1 else default_csv
    import_ap_csv_dataset(csv_file)
