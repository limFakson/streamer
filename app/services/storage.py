import boto3
from botocore.exceptions import NoCredentialsError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=f"http://{settings.MINIO_ENDPOINT}" if "minio" in settings.MINIO_ENDPOINT else None,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            region_name=settings.AWS_REGION,
        )
        self.bucket = settings.MINIO_BUCKET
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
        except:
            try:
                self.s3_client.create_bucket(Bucket=self.bucket)
                logger.info(f"Created bucket {self.bucket}")
            except Exception as e:
                logger.error(f"Could not create bucket: {e}")

    def upload_file(self, file_obj, destination_path: str, content_type: str = None):
        try:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type
            
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket,
                destination_path,
                ExtraArgs=extra_args
            )
            return True
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise e

    def generate_presigned_url(self, object_name: str, expiration=3600):
        try:
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': object_name},
                ExpiresIn=expiration
            )
            return response
        except Exception as e:
            logger.error(f"Presigned URL generation failed: {e}")
            return None

storage = StorageService()
