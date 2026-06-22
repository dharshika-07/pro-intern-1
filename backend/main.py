import os
import sys

# Ensure backend directory is in the Python path for resolving imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import os
from core.config import settings
print(f"[DEBUG MAIN] Current working directory: {os.getcwd()}", flush=True)
print(f"[DEBUG MAIN] DATABASE_URL: {settings.DATABASE_URL}", flush=True)
if settings.DATABASE_URL.startswith("sqlite:///"):
    db_rel_path = settings.DATABASE_URL.replace("sqlite:///", "")
    print(f"[DEBUG MAIN] Absolute database path: {os.path.abspath(db_rel_path)}", flush=True)
    print(f"[DEBUG MAIN] Database file exists: {os.path.exists(db_rel_path)}", flush=True)

from routers import story, job
from db.database import create_tables

create_tables()

app = FastAPI(
    title="Choose Your Own Adventure Game API",
    description="api to generate cool stories",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redocs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(story.router, prefix=settings.API_PREFIX)
app.include_router(job.router, prefix= settings.API_PREFIX)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run ("main:app", host="0.0.0.0", port=8000, reload=True)



    