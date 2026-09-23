import os
import sys
from sqlalchemy.orm import Session

# Configure UTF-8 output for Windows terminal
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import SessionLocal
from app.core.schema import District

AP_DISTRICTS = [
    ("DIS-AP-01", "Alluri Sitharama Raju"),
    ("DIS-AP-02", "Anakapalli"),
    ("DIS-AP-03", "Ananthapuramu"),
    ("DIS-AP-04", "Annamayya"),
    ("DIS-AP-05", "Bapatla"),
    ("DIS-AP-06", "Chittoor"),
    ("DIS-AP-07", "Dr. B.R. Ambedkar Konaseema"),
    ("DIS-AP-08", "East Godavari"),
    ("DIS-AP-09", "Eluru"),
    ("DIS-AP-10", "Guntur"),
    ("DIS-AP-11", "Kakinada"),
    ("DIS-AP-12", "Krishna"),
    ("DIS-AP-13", "Kurnool"),
    ("DIS-AP-14", "Markapuram"),
    ("DIS-AP-15", "Nandyal"),
    ("DIS-AP-16", "Ntr"),
    ("DIS-AP-17", "Palnadu"),
    ("DIS-AP-18", "Parvathipuram Manyam"),
    ("DIS-AP-19", "Polavaram"),
    ("DIS-AP-20", "Prakasam"),
    ("DIS-AP-21", "Sri Potti Sriramulu Nellore"),
    ("DIS-AP-22", "Sri Sathya Sai"),
    ("DIS-AP-23", "Srikakulam"),
    ("DIS-AP-24", "Tirupati"),
    ("DIS-AP-25", "Visakhapatnam"),
    ("DIS-AP-26", "Vizianagaram"),
    ("DIS-AP-27", "West Godavari"),
    ("DIS-AP-28", "Y.S.R. Kadapa"),
]

def seed_ap_districts():
    db = SessionLocal()
    added = 0
    updated = 0
    try:
        print(f"📦 Seeding {len(AP_DISTRICTS)} Andhra Pradesh Districts into MySQL database...")
        for dis_id, dis_name in AP_DISTRICTS:
            existing = db.query(District).filter(District.id == dis_id).first()
            if not existing:
                # Also check by name
                existing = db.query(District).filter(District.name == dis_name).first()

            if existing:
                existing.name = dis_name
                existing.state = "Andhra Pradesh"
                updated += 1
            else:
                dis = District(
                    id=dis_id,
                    name=dis_name,
                    state="Andhra Pradesh"
                )
                db.add(dis)
                added += 1

        db.commit()
        print(f"✅ Successfully added {added} new AP Districts and updated {updated} existing records in MySQL!")
    except Exception as e:
        print(f"❌ Error seeding districts: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_ap_districts()
