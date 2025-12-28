from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from app.api.deps import get_db
from app.services.storage import storage
from app.core.celery_app import celery_app
from app.db.models import VideoJob, JobStatus
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Check the health of the system:
    - Database connection
    - Redis connection (Celery broker)
    - Object Storage connection
    """
    health_status = {
        "status": "healthy",
        "components": {
            "database": "unknown",
            "redis": "unknown",
            "storage": "unknown"
        }
    }
    
    # 1. Check Database
    try:
        db.execute(text("SELECT 1"))
        health_status["components"]["database"] = "up"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["components"]["database"] = "down"
        health_status["status"] = "unhealthy"

    # 2. Check Redis (via Celery)
    try:
        with celery_app.connection() as connection:
            connection.ensure_connection(max_retries=1)
            health_status["components"]["redis"] = "up"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health_status["components"]["redis"] = "down"
        health_status["status"] = "unhealthy"

    # 3. Check Object Storage (MinIO/S3)
    try:
        # Lightweight check: list buckets (limit 1) or just check connectivity
        storage.s3_client.list_buckets()
        health_status["components"]["storage"] = "up"
    except Exception as e:
        logger.error(f"Storage health check failed: {e}")
        health_status["components"]["storage"] = "down"
        health_status["status"] = "unhealthy"
        
    if health_status["status"] == "unhealthy":
        # We might want to return 503, but 200 with status=unhealthy is often easier for simple dashboards
        pass
        
    return health_status

@router.get("/stats")
async def system_stats(db: Session = Depends(get_db)):
    """
    Return system statistics:
    - Job counts by status
    """
    stats = {
        "jobs": {
            "queued": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0,
            "total": 0
        }
    }
    
    try:
        # Group by status
        results = db.query(VideoJob.status, func.count(VideoJob.id)).group_by(VideoJob.status).all()
        
        total = 0
        for status, count in results:
            if status in stats["jobs"]: # status is Enum or str
                stats["jobs"][status] = count
            total += count
            
        stats["jobs"]["total"] = total
        
    except Exception as e:
        logger.error(f"Failed to fetch stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch system stats")
        
    return stats
