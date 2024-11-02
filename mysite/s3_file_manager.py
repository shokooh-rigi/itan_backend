import logging
import urllib.parse
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from django.conf import settings

# Set up logging
logger = logging.getLogger(__name__)


class S3:
    def __init__(self):
        """
        Initializes the S3 class with configuration from Django settings.
        """
        self.endpoint_url = settings.AWS_S3_DOMAIN or "https://s3.us-central-1.wasabisys.com"
        self.aws_access_key_id = settings.AWS_ACCESS_KEY_ID
        self.aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
        self.region_name = settings.AWS_S3_REGION_NAME
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME

        self.s3 = boto3.resource(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name
        )

    def update_s3_resource(self) -> None:
        """
        Updates the S3 resource with the current configuration.
        """
        self.s3 = boto3.resource(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name
        )

    def get_bucket_object(self, key: str):
        """
        Generates a pre-signed URL for accessing an S3 object.

        Args:
            key (str): The key of the object in the S3 bucket.

        Returns:
            Optional[str]: A pre-signed URL for the object if it exists; otherwise, None.
        """
        try:
            url = self.s3.meta.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                HttpMethod="GET",
                ExpiresIn=3600
            )
            return urllib.parse.unquote(url)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.warning(f"Object with key '{key}' does not exist in bucket '{self.bucket_name}'.")
            else:
                logger.error(f"Failed to generate pre-signed URL for key '{key}': {e}")
            return None

    def check_object_exists(self, key: str) -> bool:
        """
        Checks if an object with the given key exists in the S3 bucket.

        Args:
            key (str): The key of the object in the S3 bucket.

        Returns:
            bool: True if the object exists, False otherwise.
        """
        try:
            self.s3.meta.client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.info(f"The object with key '{key}' does not exist.")
            else:
                logger.error(f"Error checking existence of object with key '{key}': {e}")
            return False

    def upload_file_to_bucket(self, file_name: str, key: str) -> None:
        """
        Uploads a file to the S3 bucket.

        Args:
            file_name (str): The path to the file to upload.
            key (str): The key under which to store the file in the S3 bucket.
        """
        try:
            self.s3.meta.client.upload_file(Filename=file_name, Bucket=self.bucket_name, Key=key)
            logger.info(f"File '{file_name}' uploaded to bucket '{self.bucket_name}' with key '{key}'.")
        except ClientError as e:
            logger.error(f"Failed to upload file '{file_name}' to bucket '{self.bucket_name}': {e}")

    def delete_file_from_bucket(self, key: str) -> None:
        """
        Deletes an object from the S3 bucket.

        Args:
            key (str): The key of the object to delete from the S3 bucket.
        """
        try:
            self.s3.meta.client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"File with key '{key}' deleted from bucket '{self.bucket_name}'.")
        except ClientError as e:
            logger.error(f"Failed to delete file with key '{key}' from bucket '{self.bucket_name}': {e}")
