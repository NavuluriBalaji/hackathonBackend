import os
import sys
import random
from datetime import datetime
from sqlalchemy.orm import Session

# Configure UTF-8 output for Windows terminal
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import SessionLocal
from app.core.schema import PHC, PHCDetail, District

ALL_AP_PHCS = [
    # 1. Alluri Sitharama Raju
    {"id": "PHC-AP01-01", "name": "PHC Paderu Tribal", "district_id": "DIS-AP-01", "mandal": "Paderu", "pincode": "531024", "lat": 18.0833, "lon": 82.6667, "type": "Tribal", "beds": 12, "op": 65},
    {"id": "PHC-AP01-02", "name": "PHC Araku Valley", "district_id": "DIS-AP-01", "mandal": "Araku", "pincode": "531149", "lat": 18.3333, "lon": 82.8833, "type": "Tribal", "beds": 15, "op": 80},
    {"id": "PHC-AP01-03", "name": "PHC Chintapalli", "district_id": "DIS-AP-01", "mandal": "Chintapalli", "pincode": "531111", "lat": 17.8667, "lon": 82.3500, "type": "Tribal", "beds": 10, "op": 50},
    {"id": "PHC-AP01-04", "name": "PHC Rampachodavaram", "district_id": "DIS-AP-01", "mandal": "Rampachodavaram", "pincode": "533288", "lat": 17.4333, "lon": 81.7833, "type": "Tribal", "beds": 12, "op": 55},

    # 2. Anakapalli
    {"id": "PHC-AP02-01", "name": "PHC Anakapalli Town", "district_id": "DIS-AP-02", "mandal": "Anakapalli", "pincode": "531001", "lat": 17.6889, "lon": 83.0028, "type": "Urban", "beds": 20, "op": 120},
    {"id": "PHC-AP02-02", "name": "PHC Chodavaram", "district_id": "DIS-AP-02", "mandal": "Chodavaram", "pincode": "531036", "lat": 17.8333, "lon": 82.9333, "type": "Rural", "beds": 10, "op": 60},
    {"id": "PHC-AP02-03", "name": "PHC Yelamanchili", "district_id": "DIS-AP-02", "mandal": "Yelamanchili", "pincode": "531055", "lat": 17.5500, "lon": 82.8500, "type": "Rural", "beds": 12, "op": 70},

    # 3. Ananthapuramu
    {"id": "PHC-AP03-01", "name": "PHC Guntakal Urban", "district_id": "DIS-AP-03", "mandal": "Guntakal", "pincode": "515801", "lat": 15.1667, "lon": 77.3667, "type": "Urban", "beds": 15, "op": 95},
    {"id": "PHC-AP03-02", "name": "PHC Tadipatri", "district_id": "DIS-AP-03", "mandal": "Tadipatri", "pincode": "515411", "lat": 14.9167, "lon": 78.0167, "type": "Rural", "beds": 10, "op": 55},
    {"id": "PHC-AP03-03", "name": "PHC Rayadurgam", "district_id": "DIS-AP-03", "mandal": "Rayadurgam", "pincode": "515865", "lat": 14.7000, "lon": 76.8500, "type": "Rural", "beds": 10, "op": 50},

    # 4. Annamayya
    {"id": "PHC-AP04-01", "name": "PHC Rayachoti Central", "district_id": "DIS-AP-04", "mandal": "Rayachoti", "pincode": "516269", "lat": 14.0500, "lon": 78.7500, "type": "Rural", "beds": 12, "op": 65},
    {"id": "PHC-AP04-02", "name": "PHC Rajampet", "district_id": "DIS-AP-04", "mandal": "Rajampet", "pincode": "516115", "lat": 14.1833, "lon": 79.1500, "type": "Rural", "beds": 10, "op": 60},
    {"id": "PHC-AP04-03", "name": "PHC Madanapalle Urban", "district_id": "DIS-AP-04", "mandal": "Madanapalle", "pincode": "517325", "lat": 13.5500, "lon": 78.5000, "type": "Urban", "beds": 20, "op": 110},

    # 5. Bapatla
    {"id": "PHC-AP05-01", "name": "PHC Bapatla Coastal", "district_id": "DIS-AP-05", "mandal": "Bapatla", "pincode": "522101", "lat": 15.9000, "lon": 80.4667, "type": "Rural", "beds": 10, "op": 55},
    {"id": "PHC-AP05-02", "name": "PHC Chirala", "district_id": "DIS-AP-05", "mandal": "Chirala", "pincode": "523155", "lat": 15.8167, "lon": 80.3500, "type": "Urban", "beds": 15, "op": 90},

    # 6. Chittoor
    {"id": "PHC-AP06-01", "name": "PHC Chittoor Main", "district_id": "DIS-AP-06", "mandal": "Chittoor", "pincode": "517001", "lat": 13.2167, "lon": 79.1000, "type": "Urban", "beds": 18, "op": 105},
    {"id": "PHC-AP06-02", "name": "PHC Palamaner", "district_id": "DIS-AP-06", "mandal": "Palamaner", "pincode": "517408", "lat": 13.2000, "lon": 78.7500, "type": "Rural", "beds": 10, "op": 50},

    # 7. Dr. B.R. Ambedkar Konaseema
    {"id": "PHC-AP07-01", "name": "PHC Amalapuram", "district_id": "DIS-AP-07", "mandal": "Amalapuram", "pincode": "533201", "lat": 16.5833, "lon": 82.0167, "type": "Rural", "beds": 12, "op": 75},
    {"id": "PHC-AP07-02", "name": "PHC Razole", "district_id": "DIS-AP-07", "mandal": "Razole", "pincode": "533242", "lat": 16.4833, "lon": 81.8333, "type": "Rural", "beds": 10, "op": 55},

    # 8. East Godavari
    {"id": "PHC-AP08-01", "name": "PHC Rajamahendravaram City", "district_id": "DIS-AP-08", "mandal": "Rajahmundry", "pincode": "533101", "lat": 17.0000, "lon": 81.7800, "type": "Urban", "beds": 25, "op": 140},
    {"id": "PHC-AP08-02", "name": "PHC Kovvur", "district_id": "DIS-AP-08", "mandal": "Kovvur", "pincode": "534350", "lat": 17.0167, "lon": 81.7000, "type": "Rural", "beds": 10, "op": 60},

    # 9. Eluru
    {"id": "PHC-AP09-01", "name": "PHC Eluru Central", "district_id": "DIS-AP-09", "mandal": "Eluru", "pincode": "534001", "lat": 16.7000, "lon": 81.1000, "type": "Urban", "beds": 20, "op": 115},
    {"id": "PHC-AP09-02", "name": "PHC Jangareddygudem", "district_id": "DIS-AP-09", "mandal": "Jangareddygudem", "pincode": "534447", "lat": 17.1167, "lon": 81.3000, "type": "Rural", "beds": 12, "op": 65},

    # 10. Guntur
    {"id": "PHC-AP10-01", "name": "PHC Guntur Central", "district_id": "DIS-AP-10", "mandal": "Guntur", "pincode": "522002", "lat": 16.3000, "lon": 80.4500, "type": "Urban", "beds": 25, "op": 150},
    {"id": "PHC-AP10-02", "name": "PHC Tenali", "district_id": "DIS-AP-10", "mandal": "Tenali", "pincode": "522201", "lat": 16.2333, "lon": 80.6500, "type": "Urban", "beds": 18, "op": 100},

    # 11. Kakinada
    {"id": "PHC-AP11-01", "name": "PHC Kakinada Port", "district_id": "DIS-AP-11", "mandal": "Kakinada", "pincode": "533001", "lat": 16.9833, "lon": 82.2500, "type": "Urban", "beds": 20, "op": 130},
    {"id": "PHC-AP11-02", "name": "PHC Pithapuram", "district_id": "DIS-AP-11", "mandal": "Pithapuram", "pincode": "533450", "lat": 17.1167, "lon": 82.2500, "type": "Rural", "beds": 10, "op": 55},

    # 12. Krishna
    {"id": "PHC-AP12-01", "name": "PHC Machilipatnam Port", "district_id": "DIS-AP-12", "mandal": "Machilipatnam", "pincode": "521001", "lat": 16.1833, "lon": 81.1333, "type": "Urban", "beds": 15, "op": 85},
    {"id": "PHC-AP12-02", "name": "PHC Gudivada", "district_id": "DIS-AP-12", "mandal": "Gudivada", "pincode": "521301", "lat": 16.4333, "lon": 80.9833, "type": "Rural", "beds": 12, "op": 70},

    # 13. Kurnool
    {"id": "PHC-AP13-01", "name": "PHC Kurnool City", "district_id": "DIS-AP-13", "mandal": "Kurnool", "pincode": "518001", "lat": 15.8333, "lon": 78.0333, "type": "Urban", "beds": 25, "op": 160},
    {"id": "PHC-AP13-02", "name": "PHC Adoni", "district_id": "DIS-AP-13", "mandal": "Adoni", "pincode": "518301", "lat": 15.6333, "lon": 77.2833, "type": "Urban", "beds": 15, "op": 90},

    # 14. Markapuram
    {"id": "PHC-AP14-01", "name": "PHC Markapur Town", "district_id": "DIS-AP-14", "mandal": "Markapur", "pincode": "523316", "lat": 15.7333, "lon": 79.2667, "type": "Rural", "beds": 10, "op": 60},

    # 15. Nandyal
    {"id": "PHC-AP15-01", "name": "PHC Nandyal Town", "district_id": "DIS-AP-15", "mandal": "Nandyal", "pincode": "518501", "lat": 15.4833, "lon": 78.4833, "type": "Urban", "beds": 18, "op": 105},
    {"id": "PHC-AP15-02", "name": "PHC Srisailam Tribal", "district_id": "DIS-AP-15", "mandal": "Srisailam", "pincode": "518102", "lat": 16.0833, "lon": 78.8667, "type": "Tribal", "beds": 12, "op": 50},

    # 16. Ntr
    {"id": "PHC-AP16-01", "name": "PHC Vijayawada North", "district_id": "DIS-AP-16", "mandal": "Vijayawada", "pincode": "520001", "lat": 16.5167, "lon": 80.6167, "type": "Urban", "beds": 30, "op": 180},
    {"id": "PHC-AP16-02", "name": "PHC Nandigama", "district_id": "DIS-AP-16", "mandal": "Nandigama", "pincode": "521185", "lat": 16.7833, "lon": 80.3000, "type": "Rural", "beds": 10, "op": 60},

    # 17. Palnadu
    {"id": "PHC-AP17-01", "name": "PHC Narasaraopet", "district_id": "DIS-AP-17", "mandal": "Narasaraopet", "pincode": "522601", "lat": 16.2333, "lon": 80.0500, "type": "Urban", "beds": 15, "op": 95},

    # 18. Parvathipuram Manyam
    {"id": "PHC-AP18-01", "name": "PHC Parvathipuram Tribal", "district_id": "DIS-AP-18", "mandal": "Parvathipuram", "pincode": "535501", "lat": 18.7833, "lon": 83.4333, "type": "Tribal", "beds": 15, "op": 70},

    # 19. Polavaram
    {"id": "PHC-AP19-01", "name": "PHC Polavaram Agency", "district_id": "DIS-AP-19", "mandal": "Polavaram", "pincode": "534315", "lat": 17.2500, "lon": 81.6333, "type": "Tribal", "beds": 12, "op": 50},

    # 20. Prakasam
    {"id": "PHC-AP20-01", "name": "PHC Ongole Central", "district_id": "DIS-AP-20", "mandal": "Ongole", "pincode": "523001", "lat": 15.5000, "lon": 80.0500, "type": "Urban", "beds": 20, "op": 125},

    # 21. Sri Potti Sriramulu Nellore
    {"id": "PHC-AP21-01", "name": "PHC Nellore City", "district_id": "DIS-AP-21", "mandal": "Nellore", "pincode": "524001", "lat": 14.4333, "lon": 79.9667, "type": "Urban", "beds": 25, "op": 145},
    {"id": "PHC-AP21-02", "name": "PHC Gudur Coastal", "district_id": "DIS-AP-21", "mandal": "Gudur", "pincode": "524101", "lat": 14.1500, "lon": 79.8500, "type": "Rural", "beds": 10, "op": 60},

    # 22. Sri Sathya Sai
    {"id": "PHC-AP22-01", "name": "PHC Puttaparthi", "district_id": "DIS-AP-22", "mandal": "Puttaparthi", "pincode": "515134", "lat": 14.1667, "lon": 77.8167, "type": "Rural", "beds": 12, "op": 75},

    # 23. Srikakulam
    {"id": "PHC-AP23-01", "name": "PHC Srikakulam Town", "district_id": "DIS-AP-23", "mandal": "Srikakulam", "pincode": "532001", "lat": 18.3000, "lon": 83.9000, "type": "Urban", "beds": 20, "op": 115},
    {"id": "PHC-AP23-02", "name": "PHC Loddaputti", "district_id": "DIS-AP-23", "mandal": "Ichchapuram", "pincode": "532312", "lat": 18.8667, "lon": 84.6000, "type": "Rural", "beds": 10, "op": 55},

    # 24. Tirupati
    {"id": "PHC-AP24-01", "name": "PHC Tirupati Central", "district_id": "DIS-AP-24", "mandal": "Tirupati", "pincode": "517501", "lat": 13.6288, "lon": 79.4192, "type": "Urban", "beds": 30, "op": 200},
    {"id": "PHC-AP24-02", "name": "PHC Srikalahasti", "district_id": "DIS-AP-24", "mandal": "Srikalahasti", "pincode": "517644", "lat": 13.7500, "lon": 79.7000, "type": "Urban", "beds": 15, "op": 90},

    # 25. Visakhapatnam
    {"id": "PHC-AP25-01", "name": "PHC Visakhapatnam Port", "district_id": "DIS-AP-25", "mandal": "Visakhapatnam", "pincode": "530001", "lat": 17.6868, "lon": 83.2185, "type": "Urban", "beds": 30, "op": 210},
    {"id": "PHC-AP25-02", "name": "PHC Bheemunipatnam", "district_id": "DIS-AP-25", "mandal": "Bheemunipatnam", "pincode": "531163", "lat": 17.8833, "lon": 83.4333, "type": "Rural", "beds": 12, "op": 65},

    # 26. Vizianagaram
    {"id": "PHC-AP26-01", "name": "PHC Vizianagaram Fort", "district_id": "DIS-AP-26", "mandal": "Vizianagaram", "pincode": "535001", "lat": 18.1167, "lon": 83.4167, "type": "Urban", "beds": 20, "op": 120},

    # 27. West Godavari
    {"id": "PHC-AP27-01", "name": "PHC Bhimavaram Town", "district_id": "DIS-AP-27", "mandal": "Bhimavaram", "pincode": "534201", "lat": 16.5400, "lon": 81.5200, "type": "Urban", "beds": 20, "op": 125},

    # 28. Y.S.R. Kadapa
    {"id": "PHC-AP28-01", "name": "PHC Kadapa City", "district_id": "DIS-AP-28", "mandal": "Kadapa", "pincode": "516001", "lat": 14.4667, "lon": 78.8167, "type": "Urban", "beds": 25, "op": 140},
    {"id": "PHC-AP28-02", "name": "PHC Pulivendula", "district_id": "DIS-AP-28", "mandal": "Pulivendula", "pincode": "516390", "lat": 14.4167, "lon": 78.2333, "type": "Rural", "beds": 12, "op": 70},
]

def seed_all_phcs():
    db = SessionLocal()
    added_phc = 0
    updated_phc = 0
    added_detail = 0
    try:
        print(f"📦 Seeding {len(ALL_AP_PHCS)} Primary Health Centers across all Andhra Pradesh Districts into MySQL...")
        for item in ALL_AP_PHCS:
            # Check district exists
            dis = db.query(District).filter(District.id == item["district_id"]).first()
            if not dis:
                continue

            existing_phc = db.query(PHC).filter(PHC.id == item["id"]).first()
            if existing_phc:
                existing_phc.name = item["name"]
                existing_phc.district_id = item["district_id"]
                existing_phc.mandal_name = item["mandal"]
                existing_phc.pincode = item["pincode"]
                existing_phc.latitude = item["lat"]
                existing_phc.longitude = item["lon"]
                updated_phc += 1
            else:
                phc = PHC(
                    id=item["id"],
                    name=item["name"],
                    district_id=item["district_id"],
                    mandal_name=item["mandal"],
                    pincode=item["pincode"],
                    latitude=item["lat"],
                    longitude=item["lon"]
                )
                db.add(phc)
                added_phc += 1

            # Seed or update PHC Details
            existing_detail = db.query(PHCDetail).filter(PHCDetail.phc_id == item["id"]).first()
            if not existing_detail:
                detail = PHCDetail(
                    phc_id=item["id"],
                    facility_type=item.get("type", "Rural"),
                    bed_capacity=item.get("beds", 10),
                    occupied_beds=random.randint(2, item.get("beds", 10)),
                    avg_daily_op=item.get("op", 60),
                    emergency_24x7=random.choice([True, False]),
                    cold_chain_available=True,
                    doctors_assigned=random.randint(2, 4),
                    doctors_present=random.randint(2, 4),
                    nurses_assigned=random.randint(4, 8),
                    nurses_present=random.randint(4, 8),
                    last_attendance_sync=datetime.utcnow()
                )
                db.add(detail)
                added_detail += 1

        db.commit()
        print(f"✅ Successfully added {added_phc} new PHCs, updated {updated_phc} existing PHCs, and created {added_detail} PHC Details!")
    except Exception as e:
        print(f"❌ Error seeding PHCs: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_all_phcs()
