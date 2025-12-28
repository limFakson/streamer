from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.db.models import VideoJob, JobStatus
from app.services.storage import storage
import boto3
from botocore.exceptions import ClientError
from app.core.config import settings

router = APIRouter()

from fastapi.responses import RedirectResponse

@router.get("/job/{job_id}")
async def redirect_to_master(job_id: str):
    """
    Redirects base job URL to master.m3u8 to ensure correct relative path resolution.
    """
    return RedirectResponse(url=f"/stream/job/{job_id}/master.m3u8")

@router.get("/job/{job_id}/{path:path}")
async def stream_hls_content(job_id: str, path: str, db: Session = Depends(get_db)):
    """
    Proxy HLS content (variants playlists and segments).
    Handles paths like:
    - master.m3u8
    - v0/playlist.m3u8
    - v0/segment_000.ts
    """
    remote_hls_path = f"processed/{job_id}/hls"
    key = f"{remote_hls_path}/{path}"
    
    try:
        obj = storage.s3_client.get_object(Bucket=storage.bucket, Key=key)
        
        media_type = "application/x-mpegURL" if path.endswith(".m3u8") else "video/MP2T"
        
        # Streaming response is better for Segments
        from fastapi.responses import StreamingResponse
        
        return StreamingResponse(
            obj['Body'], 
            media_type=media_type
        )
    except ClientError as e:
        raise HTTPException(status_code=404, detail="Content not found")
