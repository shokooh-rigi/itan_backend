import boto3
import botocore
from django.conf import settings


class S3:
    def __init__(self):
        self.endpoint_url = settings.AWS_S3_DOMAIN
        self.aws_access_key_id = settings.AWS_ACCESS_KEY_ID
        self.aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
        self.region_name = settings.AWS_S3_REGION_NAME
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        # self.s3 = resource('s3',
        #                    endpoint_url=self.endpoint_url,
        #                    aws_access_key_id=self.aws_access_key_id,
        #                    aws_secret_access_key=self.aws_secret_access_key,
        #                    region_name=self.region_name)
        self.s3 = boto3.client(
            's3',
            endpoint_url='https://s3.us-central-1.wasabisys.com',
            aws_access_key_id='912TIXQPRLEFEDLWGSXM',
            aws_secret_access_key='BggzC2hjvtr1DMQjjAk6k7ZnDua9wXw8B0RciN0R',
            config=botocore.config.Config(
                retries={'max_attempts': 10},  # Increase retry attempts
                read_timeout=30                # Extend read timeout duration
            )
        )

    def update_s3_resource(self):
        # self.s3 = boto3.resource('s3',
        #                    endpoint_url=self.endpoint_url,
        #                    aws_access_key_id=self.aws_access_key_id,
        #                    aws_secret_access_key=self.aws_secret_access_key,
        #                    region_name=self.region_name)
        self.s3 = boto3.client(
            's3',
            endpoint_url='https://s3.us-central-1.wasabisys.com',
            aws_access_key_id='912TIXQPRLEFEDLWGSXM',
            aws_secret_access_key='BggzC2hjvtr1DMQjjAk6k7ZnDua9wXw8B0RciN0R',
            config=botocore.config.Config(
                retries={'max_attempts': 10},  # Increase retry attempts
                read_timeout=30                # Extend read timeout duration
            )
        )

    def get_bucket_object(self, key: str):
        # return self.s3.meta.client.generate_presigned_url('get_object', Params={'Bucket': self.bucket_name,
        #                                                     'Key': key},
        #                               HttpMethod="GET")
        return self.s3.generate_presigned_url('get_object', Params={'Bucket': self.bucket_name,
                                                            'Key': key},
                                      HttpMethod="GET")

    def upload_file_to_bucket(self, file_name: str, key: str):
        return self.s3.meta.client.upload_file(Bucket=self.bucket_name, Filename=file_name, Key=key)

    def delete_file_from_bucket(self, key: str):
        return self.s3.meta.client.delete_object(Bucket=self.bucket_name, Key=key)

