import uuid
from typing import Optional
from fastapi import APIRouter,Depends, HTTPException,Cookie
from sqlalchemy.orm import Session

from db.database import get_db
from models.job import StoryJob
from schemas.job import StoryJobResponse

router =APIRouter(
    prefix="/jobs",
    tags=["jobs"]
)

@router.get("/{job_id}",response_model =StoryJobResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    import os
    import traceback
    from db.database import engine

    print(f"[TEMP LOG] GET /api/jobs/{job_id} - Request URL: /api/jobs/{job_id}", flush=True)
    print(f"[TEMP LOG] GET /api/jobs/{job_id} - job_id: {job_id}", flush=True)
    print(f"[TEMP LOG] GET /api/jobs/{job_id} - Absolute SQLite database path: {os.path.abspath(str(engine.url.database)) if engine.url.database else 'None'}", flush=True)

    try:
        job = db.query(StoryJob).filter(StoryJob.job_id == job_id).first()

        if not job:
            print(f"[TEMP LOG] GET /api/jobs/{job_id} - Response status: 404", flush=True)
            print(f"[TEMP LOG] GET /api/jobs/{job_id} - Response body: Job not found", flush=True)
            raise HTTPException(status_code =404, detail="Job not found")
        
        print(f"[TEMP LOG] GET /api/jobs/{job_id} - Job status returned: {job.status}", flush=True)
        print(f"[TEMP LOG] GET /api/jobs/{job_id} - Response status: 200", flush=True)
        print(f"[TEMP LOG] GET /api/jobs/{job_id} - Response body: job_id={job.job_id}, status={job.status}, story_id={job.story_id}", flush=True)
        return job
    except Exception as e:
        print(f"[TEMP LOG] GET /api/jobs/{job_id} - Exception: {e}", flush=True)
        if not isinstance(e, HTTPException):
            traceback.print_exc()
        raise e