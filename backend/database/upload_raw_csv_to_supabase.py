import os
import sys
from pathlib import Path
import requests

root_dir = Path(__file__).resolve().parent.parent
dataset_dir = root_dir / "dataset"

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://fcpwrmzviqrhsdgelwmk.supabase.co")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")
BUCKET_NAME = "dataset"

if not SUPABASE_SECRET_KEY:
    print("[ERROR] SUPABASE_SECRET_KEY environment variable is missing.")
    sys.exit(1)

HEADERS = {
    "apikey": SUPABASE_SECRET_KEY,
    "Authorization": f"Bearer {SUPABASE_SECRET_KEY}"
}

def upload_raw_dataset_files():
    print("======================================================================")
    print("UPLOADING RAW CSV DATASETS (23 FILES) TO SUPABASE STORAGE BUCKET 'dataset'")
    print("======================================================================")

    # 1. Ensure bucket exists
    bucket_url = f"{SUPABASE_URL}/storage/v1/bucket"
    res = requests.post(bucket_url, headers={**HEADERS, "Content-Type": "application/json"}, json={"id": BUCKET_NAME, "name": BUCKET_NAME, "public": True})
    if res.status_code in [200, 201, 409, 400]:
        print(f"[OK] Supabase storage bucket '{BUCKET_NAME}' confirmed.")

    # 2. Upload all 23 CSV files
    csv_files = list(dataset_dir.rglob("*.csv"))
    print(f"Found {len(csv_files)} CSV files across 4 folders.\n")

    uploaded = 0
    for csv_path in sorted(csv_files):
        rel_path = csv_path.relative_to(dataset_dir)
        object_path = str(rel_path).replace("\\", "/")
        
        upload_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{object_path}"
        
        with open(csv_path, "rb") as f:
            file_data = f.read()

        file_size_mb = len(file_data) / (1024 * 1024)
        print(f"Uploading [{object_path}] ({file_size_mb:.2f} MB)...")

        res_upload = requests.post(
            upload_url,
            headers={**HEADERS, "Content-Type": "text/csv", "x-upsert": "true"},
            data=file_data
        )

        if res_upload.status_code in [200, 201]:
            uploaded += 1
            print(f"  [OK] Uploaded successfully.")
        else:
            print(f"  [ERROR] Upload failed ({res_upload.status_code}): {res_upload.text}")

    print("\n======================================================================")
    print(f"SUCCESSFULLY UPLOADS COMPLETE: {uploaded} / {len(csv_files)} FILES IN SUPABASE STORAGE")
    print("======================================================================")

if __name__ == "__main__":
    upload_raw_dataset_files()
