import os
import sys
import datetime
from sqlalchemy import text
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

# Ensure app module can be imported cleanly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, Base, SessionLocal, get_db
from app.core.schema import User
from app.api.routes import router as api_router

app = FastAPI(
    title="Project Resilience — BRICS Health Supply Chain API",
    description="Sovereign Federated Learning & Inventory Optimization System for PHCs",
    version="1.0.0"
)

@app.on_event("startup")
def on_startup():
    try:
        print("🔗 Verifying / Initializing Database Schema...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database schema ready!")
    except Exception as e:
        print(f"⚠️ DB Startup initialization note: {e}")

# Enable CORS for Mobile App / Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,
)

# Register API Router
app.include_router(api_router)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Project Resilience API Server",
        "docs_url": "/docs"
    }

@app.get("/health")
def health_check():
    db_status = "ok"
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy" if db_status == "ok" else "degraded",
        "database": db_status,
        "service": "Project Resilience API Server",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
