import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from .database import Base

class District(Base):
    __tablename__ = "districts"

    id = Column(String(50), primary_key=True, index=True) # e.g. DIS-SRIKAKULAM
    name = Column(String(100), nullable=False) # e.g. Srikakulam
    state = Column(String(100), nullable=False, default="Andhra Pradesh")

    phcs = relationship("PHC", back_populates="district")

class User(Base):
    __tablename__ = "users"

    id = Column(String(50), primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    role = Column(String(50), nullable=False, default="phc_staff") # phc_staff | district_admin
    phc_id = Column(String(50), ForeignKey("phcs.id"), nullable=True)
    status = Column(String(50), nullable=False, default="active") # active | inactive
    last_login = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    phc = relationship("PHC")

class PHC(Base):
    __tablename__ = "phcs"

    id = Column(String(50), primary_key=True, index=True) # e.g. PHC-AP-01
    name = Column(String(150), nullable=False) # e.g. PHC Loddaputti
    district_id = Column(String(50), ForeignKey("districts.id"), nullable=False)
    mandal_name = Column(String(100), nullable=True) # e.g. Ichchapuram
    pincode = Column(String(20), nullable=True) # e.g. 532312
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    district = relationship("District", back_populates="phcs")
    details = relationship("PHCDetail", back_populates="phc", uselist=False)
    inventory = relationship("Inventory", back_populates="phc")

class PHCDetail(Base):
    __tablename__ = "phc_details"

    phc_id = Column(String(50), ForeignKey("phcs.id"), primary_key=True)
    facility_type = Column(String(50), default="Rural") # Rural | Urban | Tribal
    bed_capacity = Column(Integer, default=10)
    occupied_beds = Column(Integer, default=4)
    avg_daily_op = Column(Integer, default=50) # Average Daily Outpatient Volume
    emergency_24x7 = Column(Boolean, default=False)
    cold_chain_available = Column(Boolean, default=True)
    doctors_assigned = Column(Integer, default=2)
    doctors_present = Column(Integer, default=2)
    nurses_assigned = Column(Integer, default=4)
    nurses_present = Column(Integer, default=4)
    last_attendance_sync = Column(DateTime, default=datetime.datetime.utcnow)

    phc = relationship("PHC", back_populates="details")

class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(String(50), primary_key=True, index=True) # e.g. MED-AMOX-500
    name = Column(String(150), nullable=False) # e.g. Amoxicillin 500mg
    category = Column(String(100), nullable=False) # e.g. Antibiotic
    brand_name = Column(String(150), nullable=True)
    generic_name = Column(String(150), nullable=True)
    unit = Column(String(50), default="strip")
    barcode_unit = Column(String(100), unique=True, nullable=True)
    barcode_box = Column(String(100), unique=True, nullable=True)
    barcode_carton = Column(String(100), unique=True, nullable=True)

    inventory = relationship("Inventory", back_populates="medicine")

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phc_id = Column(String(50), ForeignKey("phcs.id"), nullable=False)
    medicine_id = Column(String(50), ForeignKey("medicines.id"), nullable=False)
    current_stock = Column(Integer, nullable=False, default=0)
    safety_threshold = Column(Integer, nullable=False, default=200)
    avg_daily_consumption = Column(Float, nullable=False, default=50.0)
    batch_number = Column(String(100), nullable=True)
    expiry_date = Column(String(20), nullable=True) # YYYY-MM-DD
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

    phc = relationship("PHC", back_populates="inventory")
    medicine = relationship("Medicine", back_populates="inventory")

class DispensingLog(Base):
    __tablename__ = "dispensing_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phc_id = Column(String(50), ForeignKey("phcs.id"), nullable=False)
    medicine_id = Column(String(50), ForeignKey("medicines.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    ingestion_mode = Column(String(50), default="camera_scan")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class Driver(Base):
    __tablename__ = "drivers"

    id = Column(String(50), primary_key=True, index=True) # e.g. DRV-WAR-01
    name = Column(String(150), nullable=False) # e.g. Ramesh Kumar
    phone = Column(String(20), nullable=False) # e.g. +91 98765 43210
    vehicle_type = Column(String(50), default="Cold-Chain Van") # Cold-Chain Van | Express Bike | 108 Emergency
    vehicle_number = Column(String(50), nullable=False) # e.g. TS-03-E-4012
    district_id = Column(String(50), ForeignKey("districts.id"), nullable=False)
    status = Column(String(50), default="available") # available | on_delivery | offline
    current_lat = Column(Float, nullable=True)
    current_lon = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    district = relationship("District")
    transfers = relationship("TransferRequest", back_populates="driver")

class TransferRequest(Base):
    __tablename__ = "transfers"

    id = Column(String(50), primary_key=True, index=True)
    source_phc_id = Column(String(50), ForeignKey("phcs.id"), nullable=False)
    target_phc_id = Column(String(50), ForeignKey("phcs.id"), nullable=False)
    medicine_id = Column(String(50), ForeignKey("medicines.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    distance_km = Column(Float, default=15.0)
    estimated_minutes = Column(Float, default=30.0)
    status = Column(String(50), default="proposed") # proposed | approved | in_transit | completed | rejected
    reason = Column(Text, nullable=True)
    driver_id = Column(String(50), ForeignKey("drivers.id"), nullable=True)
    handover_otp = Column(String(10), nullable=True)
    pickup_time = Column(DateTime, nullable=True)
    delivery_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    driver = relationship("Driver", back_populates="transfers")

