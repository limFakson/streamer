from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.db.models import VideoJob, JobStatus
from app.services.storage import storage
from app.workers.tasks import process_video_task
import uuid
import shutil
import os
import tempfile

router = APIRouter()

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_video(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Validate file type (basic)
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Must be a video.")

    # Create Job Entry
    job_id = uuid.uuid4()
    original_filename = file.filename
    s3_key = f"raw/{job_id}/{original_filename}"
    
    # 1. Read file and Upload to S3
    try:
        storage.upload_file(file.file, s3_key, content_type=file.content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    # 2. Save to DB
    new_job = VideoJob(
        id=job_id,
        original_filename=original_filename,
        storage_path=s3_key,
        status=JobStatus.QUEUED
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    # 3. Trigger Celery Task
    process_video_task.delay(str(job_id))

    return {
        "job_id": str(job_id),
        "status": "queued",
        "message": "Video uploaded successfully. Processing started."
    }

@router.get("/{job_id}")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": str(job.id),
        "status": job.status,
        "created_at": job.created_at,
        "meta_data": job.meta_data,
        "hls_url": f"/stream/job/{job_id}/master.m3u8" if job.status == JobStatus.COMPLETED else None
    }

@router.post("/{job_id}/retry")
def retry_job(job_id: str, db: Session = Depends(get_db)):
    """
    Retry a FAILED or PROCESSING (stuck) job.
    Resets status to QUEUED and re-queues the Celery task.
    """
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Allow retrying if Failed or Processing (user requested restart mechanism)
    # We could also include COMPLETED if they want to re-transcode, but usually safe to assume just failed/processing.
    if job.status not in [JobStatus.FAILED, JobStatus.PROCESSING, JobStatus.COMPLETED]: # Let's be permissive and allow re-running completed too if needed
        # Actually, let's stick to Failed/Processing + Completed (maybe they changed settings)
        pass

    job.status = JobStatus.QUEUED
    job.meta_data = {"retry": "manual_retry"} # Clear old error metadata potentially
    db.commit()
    db.refresh(job)

    process_video_task.delay(str(job_id))

    return {
        "job_id": str(job.id),
        "status": "queued",
        "message": "Job has been re-queued for processing."
    }
