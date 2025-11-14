from fastapi import FastAPI
from src.core.db.database import engine, Base
from src.routers import jobs

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Job Management API",
    description="RESTful API for managing job listings",
    version="1.0.0"
)

app.include_router(jobs.router)
