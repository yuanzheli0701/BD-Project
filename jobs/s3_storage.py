"""S3 Distributed Storage Module
Supports:
- LocalStack (local S3 emulation)
- AWS S3 (cloud)
- OVH Object Storage (S3-compatible)

Usage:
  Install localstack: docker run -d -p 4566:4566 localstack/localstack
  Then: python run_pipeline.py --s3
"""
import os, json
from pathlib import Path
from datetime import datetime, timezone

try:
    import boto3
    from botocore.client import Config
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

S3_ENDPOINT = os.environ.get("S3_ENDPOINT", "http://localhost:4566")
S3_BUCKET = os.environ.get("S3_BUCKET", "city-mood-weather")
S3_REGION = os.environ.get("S3_REGION", "us-east-1")
S3_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID", "test")
S3_SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "test")

def get_s3_client():
    """Get S3 client (localstack or real AWS)."""
    if not HAS_BOTO3:
        raise ImportError("boto3 not installed. Run: pip install boto3")
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        region_name=S3_REGION,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        config=Config(signature_version="s3v4"),
    )

def ensure_bucket():
    """Create bucket if not exists."""
    s3 = get_s3_client()
    try:
        s3.head_bucket(Bucket=S3_BUCKET)
    except Exception:
        s3.create_bucket(Bucket=S3_BUCKET)

def upload_file(local_path, s3_key):
    """Upload a local file to S3."""
    s3 = get_s3_client()
    s3.upload_file(str(local_path), S3_BUCKET, s3_key)
    print(f"  -> s3://{S3_BUCKET}/{s3_key}")

def upload_json(data, s3_key):
    """Upload a JSON object to S3."""
    s3 = get_s3_client()
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=json.dumps(data, ensure_ascii=False, indent=2),
        ContentType="application/json",
    )
    print(f"  -> s3://{S3_BUCKET}/{s3_key}")

def download_file(s3_key, local_path):
    """Download from S3 to local."""
    s3 = get_s3_client()
    s3.download_file(S3_BUCKET, s3_key, str(local_path))

def list_objects(prefix=""):
    """List objects in S3 bucket."""
    s3 = get_s3_client()
    resp = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)
    return [obj["Key"] for obj in resp.get("Contents", [])]

def sync_to_s3(date_str=None):
    """Sync local Data Lake to S3."""
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    ensure_bucket()
    base = Path(__file__).resolve().parent.parent / "data"

    layers = {
        "raw": ["lastfm", "weather"],
        "formatted": ["lastfm", "weather"],
        "combined": [],
    }

    for layer, sources in layers.items():
        for source in sources:
            local_dir = base / layer / source / date_str
            s3_prefix = f"{layer}/{source}/{date_str}/"
            if local_dir.exists():
                for f in local_dir.iterdir():
                    if f.is_file():
                        upload_file(f, s3_prefix + f.name)

        if not sources:  # combined layer
            local_dir = base / layer / date_str
            s3_prefix = f"{layer}/{date_str}/"
            if local_dir.exists():
                for f in local_dir.iterdir():
                    if f.is_file():
                        upload_file(f, s3_prefix + f.name)

    print(f"\nData synced to S3: s3://{S3_BUCKET}/")
    for obj in list_objects():
        print(f"  {obj}")

if __name__ == "__main__":
    sync_to_s3()
