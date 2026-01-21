"""Cloud storage integration for backups."""
import os
from typing import Optional, List
from pathlib import Path
from enum import Enum

from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


class CloudProvider(Enum):
    """Supported cloud storage providers."""
    S3 = "s3"
    GCS = "gcs"
    AZURE = "azure"
    LOCAL = "local"


class CloudStorageBackup:
    """Cloud storage backup manager."""

    def __init__(self, provider: CloudProvider, config: dict):
        """
        Initialize cloud storage backup.

        Args:
            provider: Cloud provider (S3, GCS, Azure)
            config: Provider-specific configuration
        """
        self.provider = provider
        self.config = config
        self._client = None

    def _get_s3_client(self):
        """Get AWS S3 client."""
        try:
            import boto3
            return boto3.client(
                "s3",
                aws_access_key_id=self.config.get("aws_access_key_id"),
                aws_secret_access_key=self.config.get("aws_secret_access_key"),
                region_name=self.config.get("region", "us-east-1"),
            )
        except ImportError:
            logger.error("boto3 not installed")
            raise

    def _get_gcs_client(self):
        """Get Google Cloud Storage client."""
        try:
            from google.cloud import storage
            return storage.Client(project=self.config.get("project_id"))
        except ImportError:
            logger.error("google-cloud-storage not installed")
            raise

    def _get_azure_client(self):
        """Get Azure Blob Storage client."""
        try:
            from azure.storage.blob import BlobServiceClient
            return BlobServiceClient.from_connection_string(
                self.config.get("connection_string")
            )
        except ImportError:
            logger.error("azure-storage-blob not installed")
            raise

    def upload(self, local_path: str, remote_path: str) -> bool:
        """
        Upload backup file to cloud storage.

        Args:
            local_path: Local file path
            remote_path: Remote file path/key

        Returns:
            True if successful
        """
        try:
            if self.provider == CloudProvider.S3:
                client = self._get_s3_client()
                bucket = self.config.get("bucket")
                client.upload_file(local_path, bucket, remote_path)
                logger.info("Uploaded to S3", bucket=bucket, key=remote_path)

            elif self.provider == CloudProvider.GCS:
                client = self._get_gcs_client()
                bucket = client.bucket(self.config.get("bucket"))
                blob = bucket.blob(remote_path)
                blob.upload_from_filename(local_path)
                logger.info("Uploaded to GCS", bucket=self.config.get("bucket"), blob=remote_path)

            elif self.provider == CloudProvider.AZURE:
                client = self._get_azure_client()
                container = client.get_container_client(self.config.get("container"))
                blob = container.upload_blob(name=remote_path, data=open(local_path, "rb"))
                logger.info("Uploaded to Azure", container=self.config.get("container"), blob=remote_path)

            else:
                logger.error("Unsupported provider", provider=self.provider)
                return False

            return True

        except Exception as e:
            logger.exception("Failed to upload backup", provider=self.provider, error=str(e))
            return False

    def download(self, remote_path: str, local_path: str) -> bool:
        """
        Download backup file from cloud storage.

        Args:
            remote_path: Remote file path/key
            local_path: Local file path

        Returns:
            True if successful
        """
        try:
            if self.provider == CloudProvider.S3:
                client = self._get_s3_client()
                bucket = self.config.get("bucket")
                client.download_file(bucket, remote_path, local_path)
                logger.info("Downloaded from S3", bucket=bucket, key=remote_path)

            elif self.provider == CloudProvider.GCS:
                client = self._get_gcs_client()
                bucket = client.bucket(self.config.get("bucket"))
                blob = bucket.blob(remote_path)
                blob.download_to_filename(local_path)
                logger.info("Downloaded from GCS", bucket=self.config.get("bucket"), blob=remote_path)

            elif self.provider == CloudProvider.AZURE:
                client = self._get_azure_client()
                container = client.get_container_client(self.config.get("container"))
                with open(local_path, "wb") as f:
                    blob_data = container.download_blob(remote_path)
                    blob_data.readinto(f)
                logger.info("Downloaded from Azure", container=self.config.get("container"), blob=remote_path)

            else:
                logger.error("Unsupported provider", provider=self.provider)
                return False

            return True

        except Exception as e:
            logger.exception("Failed to download backup", provider=self.provider, error=str(e))
            return False

    def list_backups(self, prefix: str = "") -> List[str]:
        """
        List available backups in cloud storage.

        Args:
            prefix: Prefix to filter backups

        Returns:
            List of backup file paths
        """
        try:
            backups = []

            if self.provider == CloudProvider.S3:
                client = self._get_s3_client()
                bucket = self.config.get("bucket")
                response = client.list_objects_v2(Bucket=bucket, Prefix=prefix)
                backups = [obj["Key"] for obj in response.get("Contents", [])]

            elif self.provider == CloudProvider.GCS:
                client = self._get_gcs_client()
                bucket = client.bucket(self.config.get("bucket"))
                blobs = bucket.list_blobs(prefix=prefix)
                backups = [blob.name for blob in blobs]

            elif self.provider == CloudProvider.AZURE:
                client = self._get_azure_client()
                container = client.get_container_client(self.config.get("container"))
                blobs = container.list_blobs(name_starts_with=prefix)
                backups = [blob.name for blob in blobs]

            return backups

        except Exception as e:
            logger.exception("Failed to list backups", provider=self.provider, error=str(e))
            return []

    def delete(self, remote_path: str) -> bool:
        """
        Delete backup from cloud storage.

        Args:
            remote_path: Remote file path/key

        Returns:
            True if successful
        """
        try:
            if self.provider == CloudProvider.S3:
                client = self._get_s3_client()
                bucket = self.config.get("bucket")
                client.delete_object(Bucket=bucket, Key=remote_path)

            elif self.provider == CloudProvider.GCS:
                client = self._get_gcs_client()
                bucket = client.bucket(self.config.get("bucket"))
                blob = bucket.blob(remote_path)
                blob.delete()

            elif self.provider == CloudProvider.AZURE:
                client = self._get_azure_client()
                container = client.get_container_client(self.config.get("container"))
                container.delete_blob(remote_path)

            logger.info("Deleted backup", provider=self.provider, path=remote_path)
            return True

        except Exception as e:
            logger.exception("Failed to delete backup", provider=self.provider, error=str(e))
            return False
