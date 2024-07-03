import boto3
import botocore
from django.conf import settings
import requests
from botocore.exceptions import ClientError
import urllib.parse


class S3:
    def __init__(self):
        # self.endpoint_url = settings.AWS_S3_DOMAIN
        # self.aws_access_key_id = settings.AWS_ACCESS_KEY_ID
        # self.aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
        # self.region_name = settings.AWS_S3_REGION_NAME
        # self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME

        # self.endpoint_url = "https://s3.us-central-1.wasabisys.com"
        self.endpoint_url = "https://s3.us-central-1.wasabisys.com"
        self.aws_access_key_id = "912TIXQPRLEFEDLWGSXM"
        self.aws_secret_access_key = "BggzC2hjvtr1DMQjjAk6k7ZnDua9wXw8B0RciN0R"
        self.region_name = "us-central-1"
        # self.region_name = "us-east-1"
        self.bucket_name = "airtab-test"


        self.s3 = boto3.resource('s3',
                           endpoint_url=self.endpoint_url,
                           aws_access_key_id=self.aws_access_key_id,
                           aws_secret_access_key=self.aws_secret_access_key,
                           region_name=self.region_name)

    def update_s3_resource(self):
        self.s3 = boto3.resource('s3',
                           endpoint_url=self.endpoint_url,
                           aws_access_key_id=self.aws_access_key_id,
                           aws_secret_access_key=self.aws_secret_access_key,
                           region_name=self.region_name)

    def get_bucket_object(self, key: str):
        # if not self.check_object_exists(key):
        #     print(f"Object with key '{key}' does not exist in bucket '{self.bucket_name}'.")
        #     return None

        url = self.s3.meta.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket_name, 'Key': key},
            HttpMethod="GET", 
            ExpiresIn=3600
        )
        # Decode the URL
        url = urllib.parse.unquote(url)

        # print("===" * 15)
        # print(f"Key: {key}")
        # print(f"URL: {url}")

        return url


    def check_object_exists(self, key: str):
        try:
            self.s3.meta.client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                print(f"The object with key '{key}' does not exist.")
            else:
                print(f"An error occurred: {e}")
            return False

    def upload_file_to_bucket(self, file_name: str, key: str):
        return self.s3.meta.client.upload_file(Bucket=self.bucket_name, Filename=file_name, Key=key)

    def delete_file_from_bucket(self, key: str):
        return self.s3.meta.client.delete_object(Bucket=self.bucket_name, Key=key)
