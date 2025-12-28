from app.core.celery_app import celery_app
from app.db.base import SessionLocal
from app.db.models import VideoJob, JobStatus
from app.services.storage import storage
from app.services.ffmpeg import ffmpeg_service
import os
import shutil
import tempfile
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, acks_late=True)
def process_video_task(self, job_id: str):
    db = SessionLocal()
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    
    if not job:
        logger.error(f"Job {job_id} not found.")
        db.close()
        return

    try:
        # Update status to processing
        job.status = JobStatus.PROCESSING
        db.commit()

        # Create temporary working directory
        with tempfile.TemporaryDirectory() as temp_dir:
            local_input_path = os.path.join(temp_dir, job.original_filename)
            output_hls_dir = os.path.join(temp_dir, "hls")
            
            # 1. Download input file from Object Storage
            logger.info(f"Downloading {job.storage_path} to {local_input_path}")
            storage.s3_client.download_file(storage.bucket, job.storage_path, local_input_path)

            # 2. Transcode
            logger.info(f"Transcoding {job_id}...")
            ffmpeg_service.transcode_to_hls(local_input_path, output_hls_dir, job_id)

            # 3. Upload Output (HLS directory) to Object Storage
            remote_hls_path = f"processed/{job_id}/hls"
            
            for root, _, files in os.walk(output_hls_dir):
                for file in files:
                    local_file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(local_file_path, output_hls_dir)
                    remote_file_key = f"{remote_hls_path}/{rel_path}"
                    
                    content_type = "application/x-mpegURL" if file.endswith(".m3u8") else "video/MP2T"
                    
                    with open(local_file_path, "rb") as f:
                        storage.upload_file(f, remote_file_key, content_type)

            # 4. Update Job
            job.status = JobStatus.COMPLETED
            job.hls_output_path = remote_hls_path
            db.commit()
            logger.info(f"Job {job_id} completed successfully.")

    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}")
        job.status = JobStatus.FAILED
        job.meta_data = {"error": str(e)}
        db.commit()
        # Retry logic could go here
    finally:
        db.close()
