import uuid
from sqlalchemy import Column, String, Float, DateTime, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import enum
from app.db.base import Base

class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class VideoJob(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    status = Column(Enum(JobStatus), default=JobStatus.QUEUED, nullable=False)
    original_filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False) # Path in S3 bucket
    hls_output_path = Column(String, nullable=True) # Directory in S3 containing playlist
    duration = Column(Float, nullable=True)
    meta_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
