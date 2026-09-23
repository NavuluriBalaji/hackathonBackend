import os
import sys
import pandas as pd
from sqlalchemy.orm import Session

# Configure UTF-8 output for Windows terminal
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure backend package can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import SessionLocal
from app.core.schema import Driver, District

def import_drivers_csv(csv_path: str):
    """
    Imports Mockaroo Drivers CSV dataset into MySQL / SQLite database.
    Expected CSV Columns: id, name, phone, vehicle_type, vehicle_number, district_id, status, current_lat, current_lon
    """
    if not os.path.exists(csv_path):
        print(f"❌ Driver CSV file not found at: {csv_path}")
        return False

    print(f"📥 Importing Mockaroo Drivers CSV dataset: {csv_path}")
    df = pd.read_csv(csv_path)
    db = SessionLocal()

    driver_count = 0
    try:
        for idx, row in df.iterrows():
            drv_id = str(row.get("id", f"DRV-{idx+1:03d}")).strip()
            name = str(row.get("name", f"Driver #{idx+1}")).strip()
            phone = str(row.get("phone", "+91 98480 00000")).strip()
            v_type = str(row.get("vehicle_type", "Cold-Chain Van")).strip()
            v_num = str(row.get("vehicle_number", f"TS-03-E-{1000+idx}")).strip()
            dis_id = str(row.get("district_id", "DIS-01")).strip()
            status = str(row.get("status", "available")).strip()
            lat = float(row.get("current_lat", 17.0500))
            lon = float(row.get("current_lon", 79.2667))

            # Ensure district exists or fallback
            dis = db.query(District).filter(District.id == dis_id).first()
            if not dis:
                dis_id = "DIS-01" # Fallback to Nalgonda / DIS-01

            existing_drv = db.query(Driver).filter(Driver.id == drv_id).first()
            if not existing_drv:
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
                driver_count += 1
            else:
                existing_drv.name = name
                existing_drv.phone = phone
                existing_drv.vehicle_type = v_type
                existing_drv.vehicle_number = v_num
                existing_drv.status = status
                existing_drv.current_lat = lat
                existing_drv.current_lon = lon

        db.commit()
        print(f"✅ Successfully imported {driver_count} new Driver records into MySQL!")
        return True
    except Exception as e:
        print(f"❌ Error importing Drivers CSV data: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    default_csv = r"d:\dev\personal\Hackathon\drivers_mock_data.csv"
    csv_file = sys.argv[1] if len(sys.argv) > 1 else default_csv
    import_drivers_csv(csv_file)
