from boto3 import resource
from .settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_STORAGE_BUCKET_NAME, AWS_S3_ENDPOINT_URL, AWS_REGION_NAME
import environ

env = environ.Env()
environ.Env.read_env()


class S3:
    def __init__(self):
        self.endpoint_url = AWS_S3_ENDPOINT_URL
        self.aws_access_key_id = AWS_ACCESS_KEY_ID
        self.aws_secret_access_key = env('AWS_SECRET_ACCESS_KEY')
        self.region_name = AWS_REGION_NAME
        self.bucket_name = AWS_STORAGE_BUCKET_NAME
        self.s3 = resource('s3',
                           endpoint_url=self.endpoint_url,
                           aws_access_key_id=self.aws_access_key_id,
                           aws_secret_access_key=self.aws_secret_access_key,
                           region_name=self.region_name)

    def update_s3_resource(self):
        self.s3 = resource('s3',
                           endpoint_url=self.endpoint_url,
                           aws_access_key_id=self.aws_access_key_id,
                           aws_secret_access_key=self.aws_secret_access_key,
                           region_name=self.region_name)

    def get_bucket_object(self, key: str):
        return self.s3.meta.client.generate_presigned_url('get_object', Params={'Bucket': self.bucket_name,
                                                            'Key': key},
                                      HttpMethod="GET")

    def upload_file_to_bucket(self, file_name: str, key: str):
        return self.s3.meta.client.upload_file(Bucket=self.bucket_name, Filename=file_name, Key=key)

    def delete_file_from_bucket(self, key: str):
        return self.s3.meta.client.delete_object(Bucket=self.bucket_name, Key=key)

