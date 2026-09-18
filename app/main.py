import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure app module can be imported cleanly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, Base
from app.api.routes import router as api_router

# Initialize database schema if missing
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Project Resilience — BRICS Health Supply Chain API",
    description="Sovereign Federated Learning & Inventory Optimization System for PHCs",
    version="1.0.0"
)

# Enable CORS for Mobile App / Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://.*",
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
