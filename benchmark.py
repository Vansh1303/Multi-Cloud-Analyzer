"""
Multi-Cloud Storage Benchmark
Usage:
    python benchmark.py gcp              # benchmark GCP only
    python benchmark.py aws,gcp          # benchmark AWS and GCP
    python benchmark.py aws,azure,gcp    # benchmark all three
    python benchmark.py                  # interactive menu
"""

import os
import sys
import pandas as pd
import requests
from datetime import datetime
from dotenv import load_dotenv
from providers import PROVIDER_REGISTRY, check_provider_env, load_provider

load_dotenv()

# ----- Configuration -----
FILE_SIZE_MB = 5
TEST_ROUNDS = 3
CSV_FILE = "benchmark_results.csv"

# All benchmark operations in execution order
OPERATIONS = ["Upload", "Download", "Metadata", "List", "Delete"]

DATASET_URL = "https://data.wa.gov/api/views/f6w7-q2d2/rows.csv?accessType=DOWNLOAD"
DATA_DIR = "data"
DATASET_FILE = os.path.join(DATA_DIR, "dataset.csv")


def get_real_dataset():
    """Download the dataset from Data.gov if it doesn't exist."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    if not os.path.exists(DATASET_FILE):
        print(f"  Downloading real dataset (Open Government Data) ...")
        try:
            response = requests.get(DATASET_URL, timeout=30)
            response.raise_for_status()
            with open(DATASET_FILE, "wb") as f:
                f.write(response.content)
            print(f"  Dataset saved to {DATASET_FILE} ({len(response.content)/1024/1024:.2f} MB)")
        except Exception as e:
            print(f"  [Error] Failed to download dataset: {e}")
            print(f"  Falling back to generated test file.")
            # Create a fallback file if download fails
            with open(DATASET_FILE, "wb") as f:
                f.write(os.urandom(5 * 1024 * 1024))
    else:
        print(f"  Using existing dataset: {DATASET_FILE}")
    
    return DATASET_FILE


def generate_test_file(filename, size_mb):
    with open(filename, "wb") as f:
        f.write(os.urandom(size_mb * 1024 * 1024))
    print(f"  Generated {size_mb} MB test file: {filename}")


# ──────────────────────────────────────────────
#  Provider selection (CLI arg or interactive)
# ──────────────────────────────────────────────

def select_providers_interactive():
    print("\n  Multi-Cloud Benchmark - Provider Selection")
    print("=" * 50)

    keys = list(PROVIDER_REGISTRY.keys())
    for i, key in enumerate(keys, 1):
        name = PROVIDER_REGISTRY[key]["name"]
        ok, missing = check_provider_env(key)
        status = "ready" if ok else f"missing {missing}"
        marker = "+" if ok else "-"
        print(f"  {i}. {name:<8} [{marker} {status}]")

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


def init_clouds(provider_keys):
    """Load requested providers. Returns {name: (client, bucket)}."""
    clouds = {}
    for key in provider_keys:
        if key not in PROVIDER_REGISTRY:
            print(f"  Unknown provider: {key}  (options: {', '.join(PROVIDER_REGISTRY)})")
            continue
        result = load_provider(key)
        if result:
            client, bucket = result
            clouds[client.name] = (client, bucket)
    return clouds


# ──────────────────────────────────────────────
#  Benchmark runner
# ──────────────────────────────────────────────

def run_benchmark(clouds):
    if not clouds:
        print("No cloud providers available. Check your .env file.")
        return

    test_file = get_real_dataset()
    download_file = "downloaded_test.bin"
    file_size_bytes = os.path.getsize(test_file)
    file_size_mb = file_size_bytes / (1024 * 1024)

    results = []
    uploaded_urls = {}   # provider -> latest URL

    providers_str = ", ".join(clouds.keys())
    print(f"\n  Starting Benchmark")
    print(f"  Providers : {providers_str}")
    print(f"  File Size : {FILE_SIZE_MB} MB")
    print(f"  Rounds    : {TEST_ROUNDS}")
    print(f"  Operations: {', '.join(OPERATIONS)}")
    print("=" * 55)

    for round_num in range(1, TEST_ROUNDS + 1):
        print(f"\n--- Round {round_num}/{TEST_ROUNDS} ---")

        for provider, (client, bucket) in clouds.items():

            # ── Upload ──
            print(f"  [{provider}] Upload ...", end="", flush=True)
            up = client.upload_file(test_file, bucket, test_file)
            if up.elapsed > 0:
                speed = file_size_mb / up.elapsed
                uploaded_urls[provider] = up.url
                print(f" {up.elapsed:.2f}s | {speed:.2f} MB/s | {up.url}")
                results.append(_row(provider, "Upload", up.elapsed, speed, round_num, up.url, file_size_mb))
            else:
                print(" FAILED")

            # ── Download ──
            print(f"  [{provider}] Download ...", end="", flush=True)
            dl = client.download_file(bucket, test_file, download_file)
            if dl.elapsed > 0:
                speed = file_size_mb / dl.elapsed
                print(f" {dl.elapsed:.2f}s | {speed:.2f} MB/s")
                results.append(_row(provider, "Download", dl.elapsed, speed, round_num, size_mb=file_size_mb))
            else:
                print(" FAILED")

            # ── Metadata (HEAD) ──
            print(f"  [{provider}] Metadata ...", end="", flush=True)
            meta = client.get_metadata(bucket, test_file)
            if meta.elapsed > 0:
                size_info = meta.metadata.get("size_bytes", "?")
                print(f" {meta.elapsed:.3f}s | size={size_info} bytes")
                results.append(_row(provider, "Metadata", meta.elapsed, None, round_num))
            else:
                print(" FAILED")

            # ── List Objects ──
            print(f"  [{provider}] List ...", end="", flush=True)
            ls = client.list_objects(bucket, prefix="")
            if ls.elapsed > 0:
                print(f" {ls.elapsed:.3f}s | {ls.object_count} objects found")
                results.append(_row(provider, "List", ls.elapsed, None, round_num))
            else:
                print(" FAILED")

            # ── Delete ──
            print(f"  [{provider}] Delete ...", end="", flush=True)
            rm = client.delete_file(bucket, test_file)
            if rm.elapsed > 0:
                print(f" {rm.elapsed:.3f}s")
                results.append(_row(provider, "Delete", rm.elapsed, None, round_num))
            else:
                print(" FAILED")

            # cleanup local download
            if os.path.exists(download_file):
                os.remove(download_file)

    # Note: We keep the dataset file in the data/ directory instead of deleting it

    # ── Portability Test ──
    portability_data = []
    if len(clouds) >= 2:
        print("\n" + "=" * 55)
        print("  PORTABILITY TEST (Cross-Cloud Transfer)")
        print("=" * 55)
        names = list(clouds.keys())
        # Test between all unique pairs
        for i in range(len(names)):
            for j in range(len(names)):
                if i == j:
                    continue
                res = run_portability_test(clouds, names[i], names[j])
                if res:
                    portability_data.append(res)
                    # Log to results for CSV
                    results.append(_row(f"{names[i]}->{names[j]}", "Portability", res["total"], None, 1, size_mb=res.get("size_mb")))

    # ── Save CSV ──
    df = pd.DataFrame(results)
    if os.path.exists(CSV_FILE):
        df.to_csv(CSV_FILE, mode="a", header=False, index=False)
    else:
        df.to_csv(CSV_FILE, index=False)
    print(f"\n  Raw data saved to {CSV_FILE}")

    # ── Print summary ──
    print("\n--- Speed Summary (avg MB/s) ---")
    speed_df = df[df["Speed_MBps"].notna()]
    if not speed_df.empty:
        print(speed_df.groupby(["Provider", "Operation"])["Speed_MBps"].mean().to_string())

    print("\n--- Latency Summary (avg seconds) ---")
    latency_ops = df[df["Operation"].isin(["Metadata", "List", "Delete"])]
    if not latency_ops.empty:
        print(latency_ops.groupby(["Provider", "Operation"])["Time_Seconds"].mean().to_string())

    # ── Uploaded URLs ──
    if uploaded_urls:
        print("\n--- Uploaded File URLs ---")
        for prov, url in uploaded_urls.items():
            print(f"  {prov}: {url}")

    # ── Generate report ──
    report_file = generate_report(df, uploaded_urls)
    print(f"\n  Report saved to: {report_file}")


def _row(provider, operation, elapsed, speed, round_num, url=None, size_mb=None):
    return {
        "Provider": provider,
        "Operation": operation,
        "Time_Seconds": elapsed,
        "Speed_MBps": speed,
        "Size_MB": size_mb,
        "Round": round_num,
        "URL": url,
        "Timestamp": datetime.now(),
    }


def run_portability_test(clouds, source_name, dest_name):
    """Download from source and upload to destination."""
    print(f"\n  [Portability] {source_name} -> {dest_name}")
    test_file = DATASET_FILE
    dl_file = f"port_dl_{source_name}.bin"
    
    file_path = get_real_dataset()
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    
    source_client, source_bucket = clouds[source_name]
    dest_client, dest_bucket = clouds[dest_name]

    try:
        # 1. Upload to Source
        source_client.upload_file(file_path, source_bucket, "port_test.csv")
        
        # 2. Download from Source
        print(f"    Step 1: Download from {source_name} ...", end="", flush=True)
        dl = source_client.download_file(source_bucket, "port_test.csv", dl_file)
        if dl.elapsed <= 0: raise Exception("Download failed")
        print(f" {dl.elapsed:.2f}s")

        # 3. Upload to Destination
        print(f"    Step 2: Upload to {dest_name}   ...", end="", flush=True)
        up = dest_client.upload_file(dl_file, dest_bucket, "port_test.csv")
        if up.elapsed <= 0: raise Exception("Upload failed")
        print(f" {up.elapsed:.2f}s")

        total = dl.elapsed + up.elapsed
        print(f"    Total Transfer Time: {total:.2f}s")
        
        # Cleanup
        source_client.delete_file(source_bucket, "port_test.csv")
        dest_client.delete_file(dest_bucket, "port_test.csv")
        if os.path.exists(dl_file): os.remove(dl_file)
            
        return {
            "source": source_name,
            "dest": dest_name,
            "dl_time": dl.elapsed,
            "up_time": up.elapsed,
            "total": total,
            "size_mb": file_size_mb
        }
    except Exception as e:
        print(f"    FAILED: {e}")
        return None


# ──────────────────────────────────────────────
#  Report generator
# ──────────────────────────────────────────────

def generate_report(df, uploaded_urls=None):
    report_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"benchmark_report_{report_time}.txt"

    portability_df = df[df["Operation"] == "Portability"]

    pricing = {
        "AWS":   {"storage_per_gb": 0.025, "egress_per_gb": 0.09,  "free_egress_gb": 100},
        "Azure": {"storage_per_gb": 0.020, "egress_per_gb": 0.087, "free_egress_gb": 100},
        "GCP":   {"storage_per_gb": 0.023, "egress_per_gb": 0.12,  "free_egress_gb": 1},
    }

    lines = []
    w = 72
    lines.append("=" * w)
    lines.append("      MULTI-CLOUD STORAGE PERFORMANCE & LOCK-IN ANALYSIS REPORT")
    lines.append("=" * w)
    lines.append(f"  Generated  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    # Get size from CSV if available or use default
    current_size = df[df["Size_MB"].notna()]["Size_MB"].iloc[-1] if not df.empty else 0
    lines.append(f"  File Source: Open Government Data (Electric Vehicle Population)")
    lines.append(f"  File Size  : {current_size:.2f} MB")
    lines.append(f"  Rounds     : {TEST_ROUNDS}")
    lines.append(f"  Providers  : {', '.join(df['Provider'].unique())}")
    lines.append(f"  Operations : {', '.join(OPERATIONS)}")
    lines.append("=" * w)

    # 1. THROUGHPUT (upload/download)
    speed_df = df[df["Speed_MBps"].notna()]
    if not speed_df.empty:
        summary = speed_df.groupby(["Provider", "Operation"]).agg(
            Avg_Time=("Time_Seconds", "mean"),
            Min_Time=("Time_Seconds", "min"),
            Max_Time=("Time_Seconds", "max"),
            Avg_Speed=("Speed_MBps", "mean"),
            Peak_Speed=("Speed_MBps", "max"),
        )
        lines.append("\n1. THROUGHPUT BENCHMARK (Upload / Download)")
        lines.append("-" * w)
        lines.append(f"  {'Provider':<10} {'Op':<10} {'Avg(s)':<10} {'Min(s)':<10} {'Max(s)':<10} {'Avg MB/s':<10} {'Peak MB/s':<10}")
        lines.append("  " + "-" * 68)
        for (prov, op), row in summary.iterrows():
            lines.append(
                f"  {prov:<10} {op:<10} {row['Avg_Time']:<10.3f} {row['Min_Time']:<10.3f} "
                f"{row['Max_Time']:<10.3f} {row['Avg_Speed']:<10.2f} {row['Peak_Speed']:<10.2f}"
            )

    # 2. LATENCY (metadata, list, delete)
    latency_df = df[df["Operation"].isin(["Metadata", "List", "Delete"])]
    if not latency_df.empty:
        lat_summary = latency_df.groupby(["Provider", "Operation"]).agg(
            Avg_ms=("Time_Seconds", lambda x: x.mean() * 1000),
            Min_ms=("Time_Seconds", lambda x: x.min() * 1000),
            Max_ms=("Time_Seconds", lambda x: x.max() * 1000),
        )
        lines.append("\n2. LATENCY BENCHMARK (Metadata / List / Delete)")
        lines.append("-" * w)
        lines.append(f"  {'Provider':<10} {'Op':<12} {'Avg(ms)':<12} {'Min(ms)':<12} {'Max(ms)':<12}")
        lines.append("  " + "-" * 56)
        for (prov, op), row in lat_summary.iterrows():
            lines.append(
                f"  {prov:<10} {op:<12} {row['Avg_ms']:<12.1f} {row['Min_ms']:<12.1f} {row['Max_ms']:<12.1f}"
            )

    # 3. HEAD-TO-HEAD
    lines.append("\n3. HEAD-TO-HEAD COMPARISON")
    lines.append("-" * w)
    if not speed_df.empty:
        avg_speeds = speed_df.groupby(["Provider", "Operation"])["Speed_MBps"].mean().unstack()
        if "Upload" in avg_speeds.columns:
            best = avg_speeds["Upload"].idxmax()
            lines.append(f"  Fastest Upload   : {best} ({avg_speeds.loc[best, 'Upload']:.2f} MB/s)")
        if "Download" in avg_speeds.columns:
            best = avg_speeds["Download"].idxmax()
            worst = avg_speeds["Download"].idxmin()
            lines.append(f"  Fastest Download : {best} ({avg_speeds.loc[best, 'Download']:.2f} MB/s)")
            lines.append(f"  Slowest Download : {worst} ({avg_speeds.loc[worst, 'Download']:.2f} MB/s)")
    if not latency_df.empty:
        avg_lat = latency_df.groupby(["Provider", "Operation"])["Time_Seconds"].mean().unstack()
        if "Metadata" in avg_lat.columns:
            best = avg_lat["Metadata"].idxmin()
            lines.append(f"  Fastest Metadata : {best} ({avg_lat.loc[best, 'Metadata'] * 1000:.1f} ms)")
        if "Delete" in avg_lat.columns:
            best = avg_lat["Delete"].idxmin()
            lines.append(f"  Fastest Delete   : {best} ({avg_lat.loc[best, 'Delete'] * 1000:.1f} ms)")

    # 4. PORTABILITY
    if not portability_df.empty:
        lines.append("\n4. PORTABILITY BENCHMARK (Cross-Cloud Transfer)")
        lines.append("-" * w)
        lines.append(f"  {'Route':<25} {'Total Time (s)':<15}")
        lines.append("  " + "-" * 40)
        for _, row in portability_df.iterrows():
            lines.append(f"  {row['Provider']:<25} {row['Time_Seconds']:<15.2f}")

    # 5. UPLOADED FILE URLs
    if uploaded_urls:
        lines.append("\n4. UPLOADED FILE URLs (last round)")
        lines.append("-" * w)
        for prov, url in uploaded_urls.items():
            lines.append(f"  {prov:<10}: {url}")

    # 6. COST ESTIMATION
    lines.append("\n6. ESTIMATED MONTHLY COST (1 TB Storage + 1 TB Egress)")
    lines.append("-" * w)
    lines.append(f"  {'Provider':<10} {'Storage($)':<14} {'Egress($)':<14} {'Total($)':<14} {'Free Egress(GB)':<16}")
    lines.append("  " + "-" * 66)
    cost_rows = []
    # Use only "pure" providers for cost (filter out Route strings)
    base_providers = [p for p in df["Provider"].unique() if "->" not in p]
    for provider in base_providers:
        p = pricing.get(provider, {"storage_per_gb": 0, "egress_per_gb": 0, "free_egress_gb": 0})
        s_cost = 1000 * p["storage_per_gb"]
        e_cost = 1000 * p["egress_per_gb"]
        total = s_cost + e_cost
        cost_rows.append((provider, s_cost, e_cost, total, p["free_egress_gb"]))
        lines.append(f"  {provider:<10} ${s_cost:<13.2f} ${e_cost:<13.2f} ${total:<13.2f} {p['free_egress_gb']}")
    if cost_rows:
        cheapest = min(cost_rows, key=lambda x: x[3])
        lines.append(f"\n  Cheapest overall : {cheapest[0]} (${cheapest[3]:.2f}/mo)")

    # 7. LOCK-IN RISK
    lines.append("\n7. VENDOR LOCK-IN RISK ASSESSMENT")
    lines.append("-" * w)
    lock_in_notes = {
        "AWS":   "Moderate - S3 API is the de facto standard; many tools are S3-compatible.",
        "Azure": "Moderate - Blob Storage SDK is Azure-specific, but migration tools exist.",
        "GCP":   "Moderate - GCS offers S3-compatible XML API; highest egress pricing of the three.",
    }
    for provider in base_providers:
        lines.append(f"  {provider:<10}: {lock_in_notes.get(provider, 'N/A')}")
    if not speed_df.empty and "Download" in avg_speeds.columns:
        slowest = avg_speeds["Download"].idxmin()
        lines.append(f"\n  Highest lock-in risk: {slowest} (slowest egress + high egress pricing).")

    # 8. RECOMMENDATIONS
    lines.append("\n8. RECOMMENDATIONS")
    lines.append("-" * w)
    if not speed_df.empty and "Upload" in avg_speeds.columns and "Download" in avg_speeds.columns:
        bu = avg_speeds["Upload"].idxmax()
        bd = avg_speeds["Download"].idxmax()
        if bu == bd:
            lines.append(f"  {bu} leads in both upload and download speeds.")
            lines.append(f"  If cost is comparable, {bu} is the recommended primary provider.")
        else:
            lines.append(f"  {bu} is fastest for uploads; {bd} is fastest for downloads.")
            lines.append("  Consider a multi-cloud strategy to leverage each provider's strengths.")
    lines.append("  Use open formats (Parquet, JSON, etc.) to ease portability across providers.")
    lines.append("  Benchmark regularly to detect provider performance changes over time.")

    lines.append("\n" + "=" * w)
    lines.append("  END OF REPORT")
    lines.append("=" * w + "\n")

    report_text = "\n".join(lines)
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(report_text)
    return report_file


# ──────────────────────────────────────────────
#  Entry point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1:
        keys = [p.strip().lower() for p in sys.argv[1].split(",")]
    else:
        keys = select_providers_interactive()

    if not keys:
        print("No providers selected.")
        sys.exit(1)

    clouds = init_clouds(keys)
    run_benchmark(clouds)
