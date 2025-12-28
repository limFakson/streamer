from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.db.models import VideoJob, JobStatus
from app.services.storage import storage
import boto3
from botocore.exceptions import ClientError
from app.core.config import settings

router = APIRouter()

@router.get("/job/{job_id}")
async def stream_hls(job_id: str, db: Session = Depends(get_db)):
    """
    Returns the master playlist content directly or redirects.
    For MVP, we will proxy the master.m3u8 content so the player can load it.
    The segments inside should be relative, so we need to handle segment requests too 
    OR standard HLS players will request segments relative to this URL.
    
    If we return content from `/stream/job/{job_id}`, the player will resolve segments against `/stream/job/`.
    So we need a route for segments like `/stream/job/{job_id}/{segment}`.
    """
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job or job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=404, detail="Stream not ready or not found")

    # Fetch master.m3u8 from S3
    key = f"{job.hls_output_path}/master.m3u8"
    
    try:
        obj = storage.s3_client.get_object(Bucket=storage.bucket, Key=key)
        content = obj['Body'].read().decode('utf-8')
        
        return Response(content=content, media_type="application/x-mpegURL")
    except ClientError as e:
         raise HTTPException(status_code=404, detail="Playlist not found in storage")

@router.get("/job/{job_id}/{path:path}")
async def stream_hls_content(job_id: str, path: str, db: Session = Depends(get_db)):
    """
    Proxy HLS content (variants playlists and segments).
    Handles paths like:
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
