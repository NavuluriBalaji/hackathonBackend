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
from app.core.schema import PHC, Medicine, Inventory

def seed_inventory_for_all_phcs():
    db = SessionLocal()
    added_count = 0
    updated_count = 0

    try:
        all_phcs = db.query(PHC).all()
        all_medicines = db.query(Medicine).all()

        print(f"📦 Found {len(all_phcs)} total PHCs and {len(all_medicines)} total Medicines in MySQL database.")

        if not all_phcs:
            print("❌ No PHCs found in database! Please run PHC seeding script first.")
            return

        if not all_medicines:
            print("❌ No Medicines found in database! Please run Medicine seeding script first.")
            return

        # Pick top 20 essential & popular medicines to seed for EVERY PHC so every PHC has stock ledger data
        # Prioritize core essential medicine IDs if available
        priority_med_ids = ["MED-AMOX-500", "MED-PARA-650", "MED-ORS-75", "MED-INSU-100", "MED-MAL-20", "MED-OXY-10", "MED-AZI-500", "MED-CIP-500", "MED-CEF-200", "MED-AML-5", "MED-ATOR-10", "MED-MET-500"]
        
        target_medicines = [m for m in all_medicines if m.id in priority_med_ids]
        
        # Fill remaining slots up to 25 medicines per PHC from other available medicines
        remaining_meds = [m for m in all_medicines if m not in target_medicines]
        target_medicines.extend(remaining_meds[:max(0, 25 - len(target_medicines))])

        print(f"⚡ Seeding inventory stock for {len(target_medicines)} medicines across all {len(all_phcs)} PHCs...")

        for phc in all_phcs:
            for med in target_medicines:
                existing = db.query(Inventory).filter(
                    Inventory.phc_id == phc.id,
                    Inventory.medicine_id == med.id
                ).first()

                stock = random.randint(150, 1500)
                threshold = random.randint(100, 300)
                daily_cons = float(random.randint(10, 60))
                batch_no = f"BAT-2026-{random.randint(100, 999)}"
                expiry = f"202{random.randint(7, 9)}-{random.randint(1, 12):02d}-28"

                if existing:
                    # Keep existing stock if already seeded, update missing batch info
                    if existing.current_stock == 0:
                        existing.current_stock = stock
                    existing.safety_threshold = threshold
                    existing.avg_daily_consumption = daily_cons
                    if not existing.batch_number:
                        existing.batch_number = batch_no
                    if not existing.expiry_date:
                        existing.expiry_date = expiry
                    existing.last_updated = datetime.utcnow()
                    updated_count += 1
                else:
                    inv = Inventory(
                        phc_id=phc.id,
                        medicine_id=med.id,
                        current_stock=stock,
                        safety_threshold=threshold,
                        avg_daily_consumption=daily_cons,
                        batch_number=batch_no,
                        expiry_date=expiry,
                        last_updated=datetime.utcnow()
                    )
                    db.add(inv)
                    added_count += 1

        db.commit()
        print(f"✅ Successfully created {added_count} new Inventory stock records and updated {updated_count} existing records across all {len(all_phcs)} PHCs!")

    except Exception as e:
        print(f"❌ Error seeding inventory: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_inventory_for_all_phcs()
