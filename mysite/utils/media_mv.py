import boto3
import botocore
import hashlib

def calculate_s3_object_md5(s3_client, bucket_name, object_key):
    """Calculate the MD5 checksum of an object in an S3 bucket."""
    obj = s3_client.get_object(Bucket=bucket_name, Key=object_key)
    hash_md5 = hashlib.md5()
    for chunk in obj['Body'].iter_chunks(4096):
        hash_md5.update(chunk)
    return hash_md5.hexdigest()

# Initialize Wasabi S3 client
wasabi_s3 = boto3.client(
    's3',
    endpoint_url='https://s3.us-central-1.wasabisys.com',
    aws_access_key_id='912TIXQPRLEFEDLWGSXM',
    aws_secret_access_key='BggzC2hjvtr1DMQjjAk6k7ZnDua9wXw8B0RciN0R',
    config=botocore.config.Config(
        retries={'max_attempts': 10},  # Increase retry attempts
        read_timeout=30                # Extend read timeout duration
    )
)

source_bucket = 'tabtech'
destination_bucket = 'airtab-test'

# Paginate through the source bucket objects
paginator = wasabi_s3.get_paginator('list_objects_v2')
pages = paginator.paginate(Bucket=source_bucket)

# Copy objects with checksum verification
for page in pages:
    if 'Contents' in page:
        for obj in page['Contents']:
            source_key = obj['Key']
            copy_source = {'Bucket': source_bucket, 'Key': source_key}
            
            try:
                # Check if the object exists in the destination bucket
                try:
                    dest_obj = wasabi_s3.head_object(Bucket=destination_bucket, Key=source_key)
                    source_md5 = calculate_s3_object_md5(wasabi_s3, source_bucket, source_key)
                    dest_md5 = dest_obj['ETag'].strip('"')  # Remove quotes

                    # Skip if the checksum matches
                    if source_md5 == dest_md5:
                        print(f"Skipped {source_key}: already exists in {destination_bucket} with a matching checksum.")
                        continue

                except botocore.exceptions.ClientError:
                    # Destination object does not exist or is inaccessible
                    pass

                # Copy the source object to the destination
                wasabi_s3.copy(copy_source, destination_bucket, source_key)
                print(f"Copied {source_key} to {destination_bucket}")
            
            except botocore.exceptions.ClientError as error:
                print(f"Could not copy {source_key}: {error}")
            except botocore.exceptions.ReadTimeoutError as error:
                print(f"Read timeout error for {source_key}: {error}")

print('Data copy completed.')
