import os
import sys
from dotenv import load_dotenv
from cloud_manager import AWSStorage, AzureStorage, GCPStorage

# Load the bucket names from .env
load_dotenv()
AWS_BUCKET = os.getenv('AWS_BUCKET_NAME')
AZURE_CONTAINER = os.getenv('AZURE_CONTAINER_NAME')
GCP_BUCKET = os.getenv('GCP_BUCKET_NAME')

# Provider registry
PROVIDERS = {
    "aws":   {"name": "AWS",   "env_keys": ["AWS_ACCESS_KEY_ID", "AWS_BUCKET_NAME"]},
    "azure": {"name": "Azure", "env_keys": ["AZURE_STORAGE_CONNECTION_STRING", "AZURE_CONTAINER_NAME"]},
    "gcp":   {"name": "GCP",   "env_keys": ["GCP_PROJECT_ID", "GCP_BUCKET_NAME"]},
}

def create_dummy_file(filename="test_file.txt", size_kb=1):
    with open(filename, "wb") as f:
        f.write(os.urandom(size_kb * 1024))
    return filename


def _test_provider(key, filename):
    """Test upload for a single provider."""
    info = PROVIDERS[key]
    name = info["name"]

    # Check env
    for env_key in info["env_keys"]:
        if not os.getenv(env_key):
            print(f"❌ Cannot test {name}: missing {env_key} in .env")
            return

    try:
        if key == "aws":
            client, bucket = AWSStorage(), AWS_BUCKET
        elif key == "azure":
            client, bucket = AzureStorage(), AZURE_CONTAINER
        elif key == "gcp":
            client, bucket = GCPStorage(), GCP_BUCKET

        print(f"\n📋 Target {name} Bucket: {bucket}")
        print(f"Testing {name} Upload...")
        time_taken = client.upload_file(filename, bucket, filename)

        if time_taken != -1:
            print(f"✅ [{name}] Success! Time: {time_taken:.4f} seconds")
        else:
            print(f"❌ [{name}] Failed (Check logs above)")

    except Exception as e:
        print(f"❌ [{name}] Crashed: {e}")


def select_providers():
    """Interactive CLI menu to pick which providers to test."""
    print("\n☁️  Quick Upload Test - Provider Selection")
    print("=" * 45)

    keys = list(PROVIDERS.keys())
    for i, key in enumerate(keys, 1):
        name = PROVIDERS[key]["name"]
        ok = all(os.getenv(k) for k in PROVIDERS[key]["env_keys"])
        status = "✅ configured" if ok else "⚠️  not configured"
        print(f"  {i}. {name:<8} [{status}]")
    print(f"  {len(keys) + 1}. All configured providers")
    print()

    choice = input("Select providers (comma-separated numbers, e.g. 1,3): ").strip()
    selected = []
    for part in choice.split(","):
        part = part.strip()
        if not part.isdigit():
            continue
        idx = int(part)
        if idx == len(keys) + 1:
            selected = keys[:]
            break
        elif 1 <= idx <= len(keys):
            selected.append(keys[idx - 1])
    return selected


def run_test(providers=None):
    if providers is None:
        providers = select_providers()

    if not providers:
        print("No providers selected. Exiting.")
        return

    filename = create_dummy_file()
    print(f"🚀 Created dummy file: {filename}")

    for key in providers:
        _test_provider(key, filename)

    # Clean up local file
    if os.path.exists(filename):
        os.remove(filename)


if __name__ == "__main__":
    # Allow quick CLI usage:  python test_upload.py gcp  OR  python test_upload.py aws,gcp
    if len(sys.argv) > 1:
        requested = [p.strip().lower() for p in sys.argv[1].split(",")]
        invalid = [p for p in requested if p not in PROVIDERS]
        if invalid:
            print(f"Unknown provider(s): {', '.join(invalid)}  (options: aws, azure, gcp)")
        valid = [p for p in requested if p in PROVIDERS]
        run_test(valid)
    else:
        run_test()
