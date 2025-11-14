from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class JobBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Job title")
    company: str = Field(..., min_length=1, max_length=200, description="Company name")
    position: str = Field(..., min_length=1, max_length=100, description="Job position/role")
    city: str = Field(..., min_length=1, max_length=100, description="City location")
    description: Optional[str] = Field(None, description="Job description")
    requirements: Optional[str] = Field(None, description="Job requirements")
    salary: Optional[str] = Field(None, max_length=50, description="Salary information")


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    company: Optional[str] = Field(None, min_length=1, max_length=200)
    position: Optional[str] = Field(None, min_length=1, max_length=100)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    requirements: Optional[str] = None
    salary: Optional[str] = Field(None, max_length=50)


class JobResponse(JobBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

