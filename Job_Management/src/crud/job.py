from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from uuid import UUID
from src.models.job import Job
from src.schemas.job import JobCreate, JobUpdate


def get_job(db: Session, job_id: UUID) -> Job:
    return db.query(Job).filter(Job.id == job_id).first()


def get_jobs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    city: Optional[str] = None,
    position: Optional[str] = None
) -> List[Job]:
    query = db.query(Job)
    
    filters = []
    if city:
        filters.append(Job.city.ilike(f"%{city}%"))
    if position:
        filters.append(Job.position.ilike(f"%{position}%"))
    
    if filters:
        query = query.filter(and_(*filters))
    
    return query.offset(skip).limit(limit).all()


def create_job(db: Session, job: JobCreate) -> Job:
    db_job = Job(**job.model_dump())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


def update_job(db: Session, job_id: UUID, job_update: JobUpdate) -> Job:
    db_job = get_job(db, job_id)
    if not db_job:
        return None
    
    update_data = job_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_job, field, value)
    
    db.commit()
    db.refresh(db_job)
    return db_job


def delete_job(db: Session, job_id: UUID) -> bool:
    db_job = get_job(db, job_id)
    if not db_job:
        return False
    
    db.delete(db_job)
    db.commit()
    return True

