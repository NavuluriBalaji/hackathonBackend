import os
import sys
import math
import datetime
import uuid
import numpy as np

# Configure UTF-8 output for Windows terminal support
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure app module can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from scipy.optimize import linear_sum_assignment
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.schema import PHC, Inventory, Medicine, TransferRequest, PHCDetail
from app.forecasting.stockout_model import forecast_phc_stockout

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates spatial distance in kilometers between two GPS coordinates."""
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 1)

def run_redistribution_optimizer(db: Session, max_transport_radius_km: float = 45.0):
    """
    Operations Research & Linear Optimization Engine:
    Identifies 🔴 Critical Shortage PHCs and pairs them with optimal 🟢 Surplus Donor PHCs 
    using SciPy linear sum assignment (minimum-cost bipartite matching).
    Generates cold-chain Transfer Directives for District Officer approval.
    """
    print("⚙️ Running Operations Research Stock Redistribution Optimizer...")
    medicines = db.query(Medicine).all()
    created_directives = []

    for med in medicines:
        med_id = med.id

        # 1. Identify Shortage PHCs (Days Cover <= 3 days)
        shortage_phcs = []
        surplus_phcs = []

        inventories = db.query(Inventory).filter(Inventory.medicine_id == med_id).all()
        for inv in inventories:
            phc = db.query(PHC).filter(PHC.id == inv.phc_id).first()
            if not phc:
                continue

            days_cover = inv.current_stock / max(1.0, inv.avg_daily_consumption)

            if days_cover <= 3.0:
                shortage_qty = max(200, int(inv.avg_daily_consumption * 7) - inv.current_stock)
                shortage_phcs.append({
                    "phc": phc,
                    "inv": inv,
                    "shortage_qty": shortage_qty,
                    "days_cover": days_cover
                })
            elif days_cover >= 14.0 and inv.current_stock > inv.safety_threshold * 2:
                available_surplus = inv.current_stock - inv.safety_threshold
                surplus_phcs.append({
                    "phc": phc,
                    "inv": inv,
                    "surplus_qty": available_surplus,
                    "days_cover": days_cover
                })

        if not shortage_phcs or not surplus_phcs:
            continue

        # 2. Build Bipartite Cost Matrix C[i][j] = Distance + Constraints
        num_shortages = len(shortage_phcs)
        num_surplus = len(surplus_phcs)
        cost_matrix = np.full((num_shortages, num_surplus), 9999.0)

        for i, s in enumerate(shortage_phcs):
            for j, d in enumerate(surplus_phcs):
                dist = haversine_distance(
                    s["phc"].latitude or 17.0, s["phc"].longitude or 79.0,
                    d["phc"].latitude or 17.0, d["phc"].longitude or 79.0
                )
                
                if dist <= max_transport_radius_km:
                    # Cost combines transport distance + surplus capacity weight
                    cost_matrix[i, j] = dist + (100.0 / max(1, d["surplus_qty"]))

        # 3. Solve Linear Sum Assignment Problem (Hungarian / Munkres Algorithm)
        row_ind, col_ind = linear_sum_assignment(cost_matrix)

        # 4. Generate Transfer Directives
        for r, c in zip(row_ind, col_ind):
            if cost_matrix[r, c] >= 9000.0:
                continue # No feasible donor within transport radius

            shortage = shortage_phcs[r]
            donor = surplus_phcs[c]

            transfer_qty = min(shortage["shortage_qty"], donor["surplus_qty"])
            if transfer_qty <= 0:
                continue

            dist_km = haversine_distance(
                shortage["phc"].latitude or 17.0, shortage["phc"].longitude or 79.0,
                donor["phc"].latitude or 17.0, donor["phc"].longitude or 79.0
            )
            eta_mins = max(15, int(dist_km * 1.8))

            directive_id = f"TR-{uuid.uuid4().hex[:8].upper()}"

            # Check if directive already exists
            existing_tr = db.query(TransferRequest).filter(
                TransferRequest.source_phc_id == donor["phc"].id,
                TransferRequest.target_phc_id == shortage["phc"].id,
                TransferRequest.medicine_id == med_id,
                TransferRequest.status == "proposed"
            ).first()

            if not existing_tr:
                tr = TransferRequest(
                    id=directive_id,
                    source_phc_id=donor["phc"].id,
                    target_phc_id=shortage["phc"].id,
                    medicine_id=med_id,
                    quantity=transfer_qty,
                    distance_km=dist_km,
                    status="proposed",
                    reason=f"AI Redistribution Directive: {shortage['phc'].name} stockout risk critical ({shortage['days_cover']:.1f}d cover remaining). Route optimized from {donor['phc'].name} (Surplus: +{donor['surplus_qty']} units).",
                    created_at=datetime.datetime.utcnow()
                )
                db.add(tr)
                created_directives.append({
                    "directive_id": directive_id,
                    "source_phc": donor["phc"].name,
                    "target_phc": shortage["phc"].name,
                    "medicine_name": med.name,
                    "quantity": transfer_qty,
                    "distance_km": dist_km,
                    "eta_mins": eta_mins
                })

    db.commit()
    print(f"✅ Operations Research Optimization Complete! Generated {len(created_directives)} Transfer Directives.")
    return {
        "success": True,
        "directives_generated": len(created_directives),
        "data": created_directives
    }

if __name__ == "__main__":
    db = SessionLocal()
    try:
        run_redistribution_optimizer(db)
    finally:
        db.close()
