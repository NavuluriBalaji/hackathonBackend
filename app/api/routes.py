import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

import hashlib
import uuid
from app.core.database import get_db
from app.core.schema import District, PHC, PHCDetail, Medicine, Inventory, DispensingLog, TransferRequest, User
from app.forecasting.stockout_model import forecast_phc_stockout
from app.federated.server import run_federated_simulation

router = APIRouter(prefix="/api")

class SignUpRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    role: Optional[str] = "phc_staff" # "phc_staff" | "district_admin"
    phc_identifier: Optional[str] = None # Accepts PHC ID (e.g. PHC-D01-03) or PHC Name (e.g. PHC Loddaputti)

class LoginRequest(BaseModel):
    username_or_email: str
    password: str

class DispenseRequest(BaseModel):
    medicine_id: str
    quantity: int
    ingestion_mode: Optional[str] = "ui_fuzzy_search"

class StatusUpdateRequest(BaseModel):
    occupied_beds: Optional[int] = None
    doctors_present: Optional[int] = None
    nurses_present: Optional[int] = None

class CrisisRequest(BaseModel):
    district_id: Optional[str] = None
    phc_id: Optional[str] = None
    surge_factor: float = 3.0

class EmergencyRequisitionRequest(BaseModel):
    phc_id: str
    medicine_id: str
    requested_quantity: Optional[int] = 500
    reason: Optional[str] = None

def _hash_pwd(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# 0. Auth Endpoints: Signup & Login
@router.post("/auth/signup")
def signup(req: SignUpRequest, db: Session = Depends(get_db)):
    # Check if username or email exists
    existing = db.query(User).filter((User.username == req.username) | (User.email == req.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or Email already registered.")

    matched_phc_id = None
    matched_phc_name = None

    is_phc_role = "phc" in (req.role or "").lower() or "staff" in (req.role or "").lower() or "manager" in (req.role or "").lower()

    if is_phc_role:
        if not req.phc_identifier:
            raise HTTPException(status_code=400, detail="PHC Manager must specify their PHC Center (ID or Name).")
        
        # Search by exact PHC ID or fuzzy PHC Name
        phc = db.query(PHC).filter(
            (PHC.id == req.phc_identifier) | (PHC.name.ilike(f"%{req.phc_identifier}%"))
        ).first()

        if not phc:
            raise HTTPException(
                status_code=404, 
                detail=f"PHC Health Center '{req.phc_identifier}' not found in system directory. Please check PHC ID or Name."
            )
        matched_phc_id = phc.id
        matched_phc_name = phc.name

    user_id = f"USR-{uuid.uuid4().hex[:8].upper()}"
    new_user = User(
        id=user_id,
        username=req.username,
        email=req.email,
        password_hash=_hash_pwd(req.password),
        full_name=req.full_name,
        role=req.role or "phc_staff",
        phc_id=matched_phc_id,
        status="active",
        last_login=datetime.datetime.utcnow(),
        created_at=datetime.datetime.utcnow()
    )

    db.add(new_user)
    db.commit()

    return {
        "success": True,
        "message": "🎉 Account created successfully! Status is now ACTIVE.",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "role": new_user.role,
            "phc_id": new_user.phc_id,
            "phc_name": matched_phc_name,
            "status": new_user.status,
            "last_login": new_user.last_login.isoformat() if new_user.last_login else None
        }
    }

@router.post("/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    pwd_hash = _hash_pwd(req.password)
    user = db.query(User).filter(
        (User.username == req.username_or_email) | (User.email == req.username_or_email)
    ).first()

    if not user or user.password_hash != pwd_hash:
        raise HTTPException(status_code=401, detail="Invalid username/email or password.")

    # Update active status and last_login
    user.status = "active"
    user.last_login = datetime.datetime.utcnow()
    db.commit()

    phc_name = None
    if user.phc_id:
        phc = db.query(PHC).filter(PHC.id == user.phc_id).first()
        phc_name = phc.name if phc else None

    # Activities / Capabilities based on role
    capabilities = []
    role_lower = (user.role or "").lower()
    if "phc" in role_lower or "manager" in role_lower or "staff" in role_lower:
        capabilities = ["dispense_medicine", "update_phc_capacity", "view_local_inventory", "view_alerts"]
    else:
        capabilities = ["run_ai_optimizer", "approve_transfers", "inject_outbreak", "run_federated_learning", "view_all_phcs"]

    return {
        "success": True,
        "message": f"🔑 Login successful! Welcome back {user.full_name}.",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "phc_id": user.phc_id,
            "phc_name": phc_name,
            "status": user.status,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "capabilities": capabilities
        }
    }

# 1. Get All Districts
@router.get("/districts")
def get_districts(db: Session = Depends(get_db)):
    districts = db.query(District).all()
    results = []
    for d in districts:
        phc_count = db.query(PHC).filter(PHC.district_id == d.id).count()
        results.append({
            "id": d.id,
            "name": d.name,
            "state": d.state,
            "phc_count": phc_count
        })
    return {"success": True, "count": len(results), "data": results}

# 2. Get All PHCs with Bed & Staff Details
@router.get("/phcs")
def get_phcs(district_id: Optional[str] = None, search: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(PHC)
    if district_id:
        query = query.filter(PHC.district_id == district_id)
    if search:
        query = query.filter(PHC.name.ilike(f"%{search}%") | PHC.mandal_name.ilike(f"%{search}%"))
    
    phcs = query.all()
    results = []
    for p in phcs:
        details = db.query(PHCDetail).filter(PHCDetail.phc_id == p.id).first()
        low_stock_count = db.query(Inventory).filter(
            Inventory.phc_id == p.id,
            Inventory.current_stock <= Inventory.safety_threshold
        ).count()

        status_color = "red" if low_stock_count >= 2 else ("yellow" if low_stock_count == 1 else "green")

        bed_cap = getattr(details, "bed_capacity", 10) if details else 10
        occ_beds = getattr(details, "occupied_beds", 4) if details else 4
        results.append({
            "id": p.id,
            "name": p.name,
            "district_id": p.district_id,
            "district_name": p.district.name if p.district else "",
            "mandal_name": p.mandal_name or "",
            "pincode": p.pincode or "",
            "latitude": p.latitude,
            "longitude": p.longitude,
            "status_color": status_color,
            "low_stock_count": low_stock_count,
            "details": {
                "facility_type": getattr(details, "facility_type", "Rural") if details else "Rural",
                "bed_capacity": bed_cap,
                "occupied_beds": occ_beds,
                "available_beds": max(0, bed_cap - occ_beds),
                "avg_daily_op": getattr(details, "avg_daily_op", 50) if details else 50,
                "emergency_24x7": getattr(details, "emergency_24x7", False) if details else False,
                "doctors_assigned": getattr(details, "doctors_assigned", 2) if details else 2,
                "doctors_present": getattr(details, "doctors_present", 2) if details else 2,
                "nurses_assigned": getattr(details, "nurses_assigned", 4) if details else 4,
                "nurses_present": getattr(details, "nurses_present", 4) if details else 4,
            }
        })
    return {"success": True, "count": len(results), "data": results}

# 3. Get Inventory Ledger for a PHC
@router.get("/phcs/{phc_id}/inventory-ledger")
def get_phc_inventory_ledger(phc_id: str, search: Optional[str] = None, db: Session = Depends(get_db)):
    phc = db.query(PHC).filter(PHC.id == phc_id).first()
    if not phc:
        raise HTTPException(status_code=404, detail="PHC not found")

    inventories = db.query(Inventory).filter(Inventory.phc_id == phc_id).all()
    results = []
    for inv in inventories:
        med = db.query(Medicine).filter(Medicine.id == inv.medicine_id).first()
        if not med:
            continue
        
        brand = getattr(med, "brand_name", None) or med.name
        generic = getattr(med, "generic_name", None) or med.name
        
        if search:
            s = search.lower()
            m_name = med.name.lower()
            b_name = brand.lower()
            g_name = generic.lower()
            cat = med.category.lower()
            if not (s in m_name or s in b_name or s in g_name or s in cat):
                continue

        days_remaining = round(inv.current_stock / max(1.0, inv.avg_daily_consumption), 1)
        risk_level = "CRITICAL" if days_remaining <= 3 else ("WARNING" if days_remaining <= 7 else "SAFE")
        days_cover_badge = f"{int(days_remaining)}d cover"

        results.append({
            "inventory_id": inv.id,
            "phc_id": inv.phc_id,
            "medicine_id": med.id,
            "medicine_name": med.name,
            "brand_name": brand,
            "generic_name": generic,
            "category": med.category,
            "unit": med.unit,
            "current_stock": inv.current_stock,
            "safety_threshold": inv.safety_threshold,
            "avg_daily_consumption": inv.avg_daily_consumption,
            "days_remaining": days_remaining,
            "days_cover_badge": days_cover_badge,
            "risk_level": risk_level,
            "batch_number": inv.batch_number,
            "expiry_date": inv.expiry_date,
            "last_updated": inv.last_updated.isoformat() if inv.last_updated else None
        })

    return {"success": True, "phc": {"id": phc.id, "name": phc.name}, "count": len(results), "data": results}

# 4. Dispense Medicine (Stock Decrement)
@router.post("/phcs/{phc_id}/dispense-medicine")
def dispense_medicine(phc_id: str, req: DispenseRequest, db: Session = Depends(get_db)):
    inv = db.query(Inventory).filter(
        Inventory.phc_id == phc_id,
        Inventory.medicine_id == req.medicine_id
    ).first()

    if not inv:
        raise HTTPException(status_code=404, detail="Inventory item not found for this PHC")

    inv.current_stock = max(0, inv.current_stock - req.quantity)
    inv.last_updated = datetime.datetime.utcnow()

    log = DispensingLog(
        phc_id=phc_id,
        medicine_id=req.medicine_id,
        quantity=req.quantity,
        ingestion_mode=req.ingestion_mode,
        timestamp=datetime.datetime.utcnow()
    )
    db.add(log)
    db.commit()

    med = db.query(Medicine).filter(Medicine.id == req.medicine_id).first()
    days_remaining = round(inv.current_stock / max(1.0, inv.avg_daily_consumption), 1)

    return {
        "success": True,
        "message": f"Successfully dispensed {req.quantity} {med.unit if med else 'units'} of {med.name if med else req.medicine_id}",
        "updated_inventory": {
            "phc_id": phc_id,
            "medicine_id": req.medicine_id,
            "current_stock": inv.current_stock,
            "days_remaining": days_remaining,
            "days_cover_badge": f"{int(days_remaining)}d cover"
        }
    }

# 5. Update PHC Capacity & Attendance Status
@router.post("/phcs/{phc_id}/update-capacity-status")
def update_capacity_status(phc_id: str, req: StatusUpdateRequest, db: Session = Depends(get_db)):
    details = db.query(PHCDetail).filter(PHCDetail.phc_id == phc_id).first()
    if not details:
        details = PHCDetail(phc_id=phc_id)
        db.add(details)

    if req.occupied_beds is not None:
        details.occupied_beds = min(details.bed_capacity, max(0, req.occupied_beds))
        details.available_beds = max(0, details.bed_capacity - details.occupied_beds)
    if req.doctors_present is not None:
        details.doctors_present = max(0, req.doctors_present)
    if req.nurses_present is not None:
        details.nurses_present = max(0, req.nurses_present)

    details.last_attendance_sync = datetime.datetime.utcnow()
    db.commit()

    return {
        "success": True,
        "message": "PHC capacity and attendance status updated successfully",
        "details": {
            "phc_id": phc_id,
            "occupied_beds": details.occupied_beds,
            "available_beds": details.bed_capacity - details.occupied_beds,
            "doctors_present": details.doctors_present,
            "nurses_present": details.nurses_present
        }
    }

# 6. Inject Outbreak Simulation
@router.post("/simulation/inject-outbreak")
def inject_outbreak(req: CrisisRequest, db: Session = Depends(get_db)):
    query = db.query(Inventory).filter(Inventory.medicine_id.in_(["MED-PARA-650", "MED-ORS-75"]))
    if req.phc_id:
        query = query.filter(Inventory.phc_id == req.phc_id)
    elif req.district_id:
        phc_ids = [p.id for p in db.query(PHC).filter(PHC.district_id == req.district_id).all()]
        query = query.filter(Inventory.phc_id.in_(phc_ids))

    affected_rows = 0
    for inv in query.all():
        inv.avg_daily_consumption = round(inv.avg_daily_consumption * req.surge_factor, 1)
        inv.current_stock = max(0, int(inv.current_stock * 0.4))
        inv.last_updated = datetime.datetime.utcnow()
        affected_rows += 1

    db.commit()
    return {
        "success": True,
        "message": f"🚨 Outbreak Injected: Disease surge factor {req.surge_factor}x applied to {affected_rows} inventory items!",
        "affected_items": affected_rows
    }

# 7. Execute Sovereign Federated Learning Simulation
@router.post("/federated/execute-federated-learning")
def execute_federated_learning(num_districts: int = Query(default=5), num_rounds: int = Query(default=3)):
    result = run_federated_simulation(num_districts=num_districts, num_rounds=num_rounds)
    return {
        "success": True,
        "message": f"🌐 Sovereign Federated Learning (FedAvg) completed across {num_districts} District Nodes over {num_rounds} rounds!",
        "federated_summary": result
    }

# 8. Get Stock Transfer Directives
@router.get("/redistribution/transfer-directives")
def get_transfer_directives(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(TransferRequest)
    if status:
        query = query.filter(TransferRequest.status == status)
    
    transfers = query.all()
    results = []
    for t in transfers:
        src = db.query(PHC).filter(PHC.id == t.source_phc_id).first()
        tgt = db.query(PHC).filter(PHC.id == t.target_phc_id).first()
        med = db.query(Medicine).filter(Medicine.id == t.medicine_id).first()
        results.append({
            "id": t.id,
            "source_phc_id": t.source_phc_id,
            "source_phc_name": src.name if src else "",
            "target_phc_id": t.target_phc_id,
            "target_phc_name": tgt.name if tgt else "",
            "medicine_id": t.medicine_id,
            "medicine_name": med.name if med else "",
            "quantity": t.quantity,
            "distance_km": t.distance_km,
            "status": t.status,
            "ai_confidence_pct": 94,
            "eta_mins": int(t.distance_km * 1.8),
            "reason": t.reason,
            "created_at": t.created_at.isoformat() if t.created_at else None
        })
    return {"success": True, "count": len(results), "data": results}

# 9. Approve Stock Transfer Directive
@router.post("/redistribution/approve-transfer")
def approve_transfer(transfer_id: str = Query(...), db: Session = Depends(get_db)):
    t = db.query(TransferRequest).filter(TransferRequest.id == transfer_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Transfer directive not found")

    t.status = "approved"

    src_inv = db.query(Inventory).filter(Inventory.phc_id == t.source_phc_id, Inventory.medicine_id == t.medicine_id).first()
    tgt_inv = db.query(Inventory).filter(Inventory.phc_id == t.target_phc_id, Inventory.medicine_id == t.medicine_id).first()

    if src_inv and src_inv.current_stock >= t.quantity:
        src_inv.current_stock -= t.quantity
    if tgt_inv:
        tgt_inv.current_stock += t.quantity

    db.commit()
    return {"success": True, "message": f"✅ Directive {transfer_id} approved! Cold-chain transit dispatched."}

from app.redistribution.engine import run_redistribution_optimizer

# 11. Execute Operations Research Stock Redistribution Optimizer (Model 3)
@router.post("/redistribution/execute-optimizer")
def execute_optimizer(max_transport_radius_km: float = Query(default=45.0), db: Session = Depends(get_db)):
    result = run_redistribution_optimizer(db=db, max_transport_radius_km=max_transport_radius_km)
    
    # Query all active proposed transfer directives so user sees pending directives even if no NEW ones were generated on this run
    pending = db.query(TransferRequest).filter(TransferRequest.status == "proposed").all()
    pending_data = []
    for t in pending:
        src = db.query(PHC).filter(PHC.id == t.source_phc_id).first()
        tgt = db.query(PHC).filter(PHC.id == t.target_phc_id).first()
        med = db.query(Medicine).filter(Medicine.id == t.medicine_id).first()
        pending_data.append({
            "id": t.id,
            "source_phc_name": src.name if src else t.source_phc_id,
            "target_phc_name": tgt.name if tgt else t.target_phc_id,
            "medicine_name": med.name if med else t.medicine_id,
            "quantity": t.quantity,
            "distance_km": t.distance_km,
            "status": t.status,
            "reason": t.reason
        })

    msg = f"⚙️ Optimization Complete! Generated {result['directives_generated']} new directives. ({len(pending_data)} total proposed directives pending approval)."
    
    return {
        "success": True,
        "message": msg,
        "optimization_summary": {
            "new_directives_generated": result["directives_generated"],
            "total_pending_directives": len(pending_data),
            "new_data": result["data"],
            "all_pending_directives": pending_data
        }
    }

# 12. Submit Emergency Stock Requisition to District Portal Queue
@router.post("/redistribution/request-emergency-stock")
def request_emergency_stock(req: EmergencyRequisitionRequest, db: Session = Depends(get_db)):
    phc = db.query(PHC).filter(PHC.id == req.phc_id).first()
    med = db.query(Medicine).filter(Medicine.id == req.medicine_id).first()

    if not phc or not med:
        raise HTTPException(status_code=404, detail="PHC or Medicine not found")

    # Find donor PHC in same district or fallback
    donor_phc = db.query(PHC).filter(PHC.district_id == phc.district_id, PHC.id != phc.id).first()
    donor_id = donor_phc.id if donor_phc else "PHC-D01-01"

    directive_id = f"TR-{uuid.uuid4().hex[:8].upper()}"
    tr = TransferRequest(
        id=directive_id,
        source_phc_id=donor_id,
        target_phc_id=phc.id,
        medicine_id=med.id,
        quantity=req.requested_quantity or 500,
        distance_km=18.5,
        status="proposed",
        reason=req.reason or f"🚨 URGENT PHC REQUISITION: Critical low stock alert at {phc.name} for {med.name}. Queued for District Officer analysis.",
        created_at=datetime.datetime.utcnow()
    )

    db.add(tr)
    db.commit()

    return {
        "success": True,
        "message": f"🚨 Emergency stock requisition for {med.name} pushed to District Portal Queue! Directive ID: {directive_id}",
        "directive_id": directive_id
    }
