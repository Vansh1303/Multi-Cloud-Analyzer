import os
import time
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from cloud_manager import AWSStorage, AzureStorage

# Load config
load_dotenv()
AWS_BUCKET = os.getenv('AWS_BUCKET_NAME')
AZURE_CONTAINER = os.getenv('AZURE_CONTAINER_NAME')

# Configuration
FILE_SIZE_MB = 5  # Size of test file
TEST_ROUNDS = 3   # How many times to repeat the test (for accuracy)
CSV_FILE = "benchmark_results.csv"

def generate_test_file(filename, size_mb):
    """Creates a dummy file of specific size"""
    with open(filename, "wb") as f:
        f.write(os.urandom(size_mb * 1024 * 1024))
    print(f"📦 Generated {size_mb}MB test file: {filename}")

def run_benchmark():
    test_file = "benchmark_test.bin"
    download_file = "downloaded_test.bin"
    generate_test_file(test_file, FILE_SIZE_MB)
    
    results = []
    
    # Initialize Clouds
    clouds = {
        "AWS": (AWSStorage(), AWS_BUCKET),
        "Azure": (AzureStorage(), AZURE_CONTAINER)
    }

    print(f"\n🚀 Starting Benchmark (Size: {FILE_SIZE_MB}MB, Rounds: {TEST_ROUNDS})...\n")

    for round_num in range(1, TEST_ROUNDS + 1):
        print(f"--- Round {round_num} ---")
        
        for provider, (client, bucket) in clouds.items():
            # 1. UPLOAD TEST
            print(f"   📤 Uploading to {provider}...", end="", flush=True)
            up_time = client.upload_file(test_file, bucket, test_file)
            
            if up_time != -1:
                up_speed = FILE_SIZE_MB / up_time
                print(f" Done ({up_time:.2f}s | {up_speed:.2f} MB/s)")
                results.append({
                    "Provider": provider,
                    "Operation": "Upload",
                    "Time_Seconds": up_time,
                    "Speed_MBps": up_speed,
                    "Size_MB": FILE_SIZE_MB,
                    "Round": round_num,
                    "Timestamp": datetime.now()
                })
            
            # 2. DOWNLOAD TEST
            print(f"   📥 Downloading from {provider}...", end="", flush=True)
            down_time = client.download_file(bucket, test_file, download_file)
            
            if down_time != -1:
                down_speed = FILE_SIZE_MB / down_time
                print(f" Done ({down_time:.2f}s | {down_speed:.2f} MB/s)")
                results.append({
                    "Provider": provider,
                    "Operation": "Download",
                    "Time_Seconds": down_time,
                    "Speed_MBps": down_speed,
                    "Size_MB": FILE_SIZE_MB,
                    "Round": round_num,
                    "Timestamp": datetime.now()
                })

    # Cleanup
    if os.path.exists(test_file): os.remove(test_file)
    if os.path.exists(download_file): os.remove(download_file)

    # Save Results
    df = pd.DataFrame(results)
    if os.path.exists(CSV_FILE):
        df.to_csv(CSV_FILE, mode='a', header=False, index=False)
    else:
        df.to_csv(CSV_FILE, index=False)

    print(f"\n✅ Benchmark Complete! Data saved to {CSV_FILE}")
    print("\n--- Summary ---")
    print(df.groupby(["Provider", "Operation"])["Speed_MBps"].mean())

if __name__ == "__main__":
    run_benchmark()