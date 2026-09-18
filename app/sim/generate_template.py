import os
import sys
import pandas as pd

# Configure UTF-8 output for Windows terminal support
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

OUTPUT_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "PHC_Master_Template.xlsx")

# Sample Datasets for Excel Template
MEDICINES_DATA = [
    {"id": "MED-AMOX-500", "name": "Amoxicillin 500mg", "category": "Antibiotic", "unit": "strip", "barcode_unit": "QR_STRIP_AMOX_500", "barcode_box": "QR_BOX_AMOX_500", "barcode_carton": "QR_CARTON_AMOX_500"},
    {"id": "MED-PARA-650", "name": "Paracetamol 650mg", "category": "Antipyretic", "unit": "strip", "barcode_unit": "QR_STRIP_PARA_650", "barcode_box": "QR_BOX_PARA_650", "barcode_carton": "QR_CARTON_PARA_650"},
    {"id": "MED-ORS-75", "name": "ORS Hydration Sachet 21g", "category": "Rehydration", "unit": "sachet", "barcode_unit": "QR_STRIP_ORS_75", "barcode_box": "QR_BOX_ORS_75", "barcode_carton": "QR_CARTON_ORS_75"},
    {"id": "MED-INSU-100", "name": "Human Insulin 100IU/ml", "category": "Diabetes", "unit": "vial", "barcode_unit": "QR_STRIP_INSU_100", "barcode_box": "QR_BOX_INSU_100", "barcode_carton": "QR_CARTON_INSU_100"}
]

DISTRICTS_PHCS_DATA = [
    {"district_id": "DIS-01", "district_name": "Nalgonda", "state": "Telangana", "phc_id": "PHC-D01-01", "phc_name": "Chityal Primary Health Centre", "latitude": 17.2341, "longitude": 79.1234, "bed_capacity": 30},
    {"district_id": "DIS-01", "district_name": "Nalgonda", "state": "Telangana", "phc_id": "PHC-D01-02", "phc_name": "Nakrekal Primary Health Centre", "latitude": 17.1654, "longitude": 79.4321, "bed_capacity": 25},
    {"district_id": "DIS-02", "district_name": "Khammam", "state": "Telangana", "phc_id": "PHC-D02-01", "phc_name": "Wyra Area Health Centre", "latitude": 17.2100, "longitude": 80.2200, "bed_capacity": 50}
]

INVENTORY_DATA = [
    {"phc_id": "PHC-D01-01", "medicine_id": "MED-AMOX-500", "current_stock": 1200, "safety_threshold": 350, "avg_daily_consumption": 50.0, "batch_number": "BAT-2026-X101", "expiry_date": "2026-12-31"},
    {"phc_id": "PHC-D01-01", "medicine_id": "MED-PARA-650", "current_stock": 4500, "safety_threshold": 500, "avg_daily_consumption": 110.0, "batch_number": "BAT-2026-X102", "expiry_date": "2027-03-15"},
    {"phc_id": "PHC-D01-02", "medicine_id": "MED-PARA-650", "current_stock": 180, "safety_threshold": 500, "avg_daily_consumption": 95.0, "batch_number": "BAT-2026-X103", "expiry_date": "2026-11-20"}
]

def generate_template():
    df_meds = pd.DataFrame(MEDICINES_DATA)
    df_phcs = pd.DataFrame(DISTRICTS_PHCS_DATA)
    df_inv = pd.DataFrame(INVENTORY_DATA)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        df_meds.to_excel(writer, sheet_name="Medicines", index=False)
        df_phcs.to_excel(writer, sheet_name="Districts_PHCs", index=False)
        df_inv.to_excel(writer, sheet_name="Inventory", index=False)

    print(f"✅ Excel Master Template successfully generated: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_template()
