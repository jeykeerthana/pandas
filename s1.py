import os
import argparse
import pandas as pd
import boto3
from botocore.exceptions import NoCredentialsError


def connect_to_aws(profile=None, access_key=None, secret_key=None, region=None):
    """Create an AWS session.

    Priority (highest -> lowest): explicit args -> env vars -> AWS config/instance role.
    """
    # Resolve region
    region = region or os.getenv("AWS_DEFAULT_REGION", "us-east-1")

    # Prefer explicit credentials passed as args
    if access_key and secret_key:
        return boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )

    # Otherwise check environment variables
    aws_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_profile = profile or os.getenv("AWS_PROFILE")

    if aws_key and aws_secret:
        return boto3.Session(
            aws_access_key_id=aws_key,
            aws_secret_access_key=aws_secret,
            region_name=region,
        )

    # Otherwise try the AWS CLI/profile
    if aws_profile:
        return boto3.Session(profile_name=aws_profile, region_name=region)

    # Fall back to default session (could use instance role / shared config)
    return boto3.Session(region_name=region)


def upload_csv_to_s3(csv_file_path, bucket_name, object_key=None, **aws_kwargs):
    """Read a CSV and upload it to an S3 bucket on AWS.

    aws_kwargs are forwarded to connect_to_aws (profile, access_key, secret_key, region).
    """
    if object_key is None:
        object_key = os.path.basename(csv_file_path)

    try:
        df = pd.read_csv(csv_file_path)
        print("CSV loaded successfully:")
        print(df.head())

        session = connect_to_aws(**aws_kwargs)
        s3 = session.client("s3")
        s3.upload_file(csv_file_path, bucket_name, object_key)

        print(f"File uploaded to s3://{bucket_name}/{object_key}")

    except FileNotFoundError:
        print(f"CSV file not found: {csv_file_path}")
    except NoCredentialsError:
        print("AWS credentials not found. Configure AWS CLI or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.")
    except Exception as e:
        print(f"Upload failed: {e}")


def parse_args():
    p = argparse.ArgumentParser(description="Upload a CSV file to S3 (uses boto3).")
    p.add_argument("--file", "-f", dest="csv_file", default="customers.csv",
                   help="Path to the CSV file to upload (default: customers.csv)")
    p.add_argument("--bucket", "-b", dest="bucket", required=True,
                   help="Target S3 bucket name")
    p.add_argument("--key", "-k", dest="key", default=None,
                   help="S3 object key (default: basename of the file)")

    creds = p.add_argument_group('aws credentials')
    creds.add_argument("--profile", dest="profile", help="AWS CLI profile to use")
    creds.add_argument("--access-key", dest="access_key", help="AWS access key id")
    creds.add_argument("--secret-key", dest="secret_key", help="AWS secret access key")
    creds.add_argument("--region", dest="region", help="AWS region (overrides AWS_DEFAULT_REGION)")

    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Run the upload with provided args — credentials fall back to env/cli if not given
    upload_csv_to_s3(
        args.csv_file,
        args.bucket,
        object_key=args.key,
        profile=args.profile,
        access_key=args.access_key,
        secret_key=args.secret_key,
        region=args.region,
    )
