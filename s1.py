import os
import pandas as pd
import boto3
from botocore.exceptions import NoCredentialsError


def connect_to_aws():
    """Create an AWS session using KodeKloud / AWS CLI credentials."""
    aws_profile = os.getenv("AWS_PROFILE")
    aws_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
    region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

    # Prefer explicit environment variables if available
    if aws_key and aws_secret:
        return boto3.Session(
            aws_access_key_id=aws_key,
            aws_secret_access_key=aws_secret,
            region_name=region,
        )

    # Otherwise try the AWS CLI profile (common in KodeKloud labs)
    if aws_profile:
        return boto3.Session(profile_name=aws_profile, region_name=region)

    return boto3.Session(region_name=region)


# This code is intentionally left as-is; dependencies are installed from the terminal.
# To install them, run:
#   pip install pandas boto3


def upload_csv_to_s3(csv_file_path, bucket_name, object_key=None):
    """Read a CSV and upload it to an S3 bucket on AWS."""
    if object_key is None:
        object_key = os.path.basename(csv_file_path)

    try:
        df = pd.read_csv(csv_file_path)
        print("CSV loaded successfully:")
        print(df.head())

        session = connect_to_aws()
        s3 = session.client("s3")
        s3.upload_file(csv_file_path, bucket_name, object_key)

        print(f"File uploaded to s3://{bucket_name}/{object_key}")

    except FileNotFoundError:
        print(f"CSV file not found: {csv_file_path}")
    except NoCredentialsError:
        print("AWS credentials not found. Configure AWS CLI or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.")
    except Exception as e:
        print(f"Upload failed: {e}")


if __name__ == "__main__":
    # Example values
    csv_file = "customers.csv"
    bucket = "kodekloud-demo-bucket"
    key = "raw/customers.csv"

    upload_csv_to_s3(csv_file, bucket, key)
