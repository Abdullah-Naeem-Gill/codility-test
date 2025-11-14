from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from src.core.db.database import get_db
from src.schemas.job import JobCreate, JobUpdate, JobResponse
from src.crud import job as crud

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=List[JobResponse])
def get_jobs(
    city: Optional[str] = Query(None, description="Filter by city"),
    position: Optional[str] = Query(None, description="Filter by position"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    jobs = crud.get_jobs(db, skip=skip, limit=limit, city=city, position=position)
    return jobs


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: UUID, db: Session = Depends(get_db)):
    db_job = crud.get_job(db, job_id=job_id)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return db_job


@router.post("", response_model=JobResponse, status_code=201)
def create_job(job: JobCreate, db: Session = Depends(get_db)):
    return crud.create_job(db=db, job=job)


@router.put("/{job_id}", response_model=JobResponse)
def update_job(job_id: UUID, job_update: JobUpdate, db: Session = Depends(get_db)):
    db_job = crud.update_job(db, job_id=job_id, job_update=job_update)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return db_job


@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: UUID, db: Session = Depends(get_db)):
    success = crud.delete_job(db, job_id=job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    return None

