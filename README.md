# Multi-Cloud Storage Performance & Lock-In Analyzer

A benchmarking tool that compares the **performance**, **cost**, and **vendor lock-in risk** of three major cloud storage providers:

- **Amazon S3** (AWS)
- **Azure Blob Storage** (Microsoft Azure)
- **Google Cloud Storage** (GCP)

## What Gets Benchmarked

Each provider is tested across **5 standard cloud storage operations**:

| Operation | What it measures |
|---|---|
| **Upload** | Time and throughput (MB/s) to push a file to the cloud. Returns the uploaded file URL. |
| **Download** | Time and throughput (MB/s) to pull the file back (egress speed). |
| **Metadata** | Latency of a HEAD request — get object size, type, etag without downloading. |
| **List** | Latency to list all objects in the bucket. |
| **Delete** | Latency to delete an object from the bucket. |

All 5 operations run per provider, per round. Default: 3 rounds with a 5 MB test file.

## Project Structure

```
Multi-Cloud-Analyzer/
├── providers/                # Provider implementations (one file per cloud)
│   ├── __init__.py           # Provider registry, lazy loading
│   ├── base.py               # Abstract base class + result dataclasses
│   ├── aws.py                # Amazon S3
│   ├── azure.py              # Azure Blob Storage
│   └── gcp.py                # Google Cloud Storage
├── benchmark.py              # Single CLI entry point — runs everything
├── cloud_manager.py          # Backward-compat shim (re-exports providers)
├── dashboard.py              # Streamlit interactive dashboard
├── debug_env.py              # Verify environment variables
├── requirements.txt          # Python dependencies
├── .env                      # Your credentials (fill this in)
├── gcp-key.json              # GCP service account key (you provide this)
└── README.md
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure `.env`

Fill in credentials **only for the providers you want to test**. Comment out or leave blank the rest — they'll be skipped automatically.

| Variable | Provider | Description |
|---|---|---|
| `AWS_ACCESS_KEY_ID` | AWS | IAM access key |
| `AWS_SECRET_ACCESS_KEY` | AWS | IAM secret key |
| `AWS_REGION` | AWS | Region (default: `ap-southeast-1`) |
| `AWS_BUCKET_NAME` | AWS | S3 bucket name |
| `AZURE_STORAGE_CONNECTION_STRING` | Azure | Full connection string |
| `AZURE_CONTAINER_NAME` | Azure | Blob container name |
| `GCP_PROJECT_ID` | GCP | Google Cloud project ID |
| `GCP_BUCKET_NAME` | GCP | GCS bucket name |
| `GCP_KEY_PATH` | GCP | *(Optional)* Path to service account key (defaults to `./gcp-key.json`) |

### 3. GCP Service Account Key

1. Go to [GCP Console > IAM > Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Create a service account with **Storage Object Admin** role
3. Generate a JSON key and save it as `gcp-key.json` in this folder

### 4. Verify Setup

```bash
python debug_env.py
```

## Usage

### Run the Benchmark

**One command does everything** — upload, download, metadata, list, delete, CSV, and report:

```bash
# GCP only
python benchmark.py gcp

# AWS and GCP
python benchmark.py aws,gcp

# All three
python benchmark.py aws,azure,gcp

# Interactive menu (shows which providers are configured)
python benchmark.py
```

**What happens when you run it:**

```
  Starting Benchmark
  Providers : GCP
  File Size : 5 MB
  Rounds    : 3
  Operations: Upload, Download, Metadata, List, Delete
=======================================================

--- Round 1/3 ---
  [GCP] Upload ... 1.42s | 3.52 MB/s | https://storage.googleapis.com/my-bucket/benchmark_test.bin
  [GCP] Download ... 0.89s | 5.62 MB/s
  [GCP] Metadata ... 0.187s | size=5242880 bytes
  [GCP] List ... 0.243s | 12 objects found
  [GCP] Delete ... 0.156s
  ...
```

**Output files:**
- `benchmark_results.csv` — Raw data with all metrics + uploaded file URLs
- `benchmark_report_<timestamp>.txt` — Full analysis report

### Interactive Menu

Running without arguments shows a menu with live config status:

```
  Multi-Cloud Benchmark - Provider Selection
==================================================
  1. AWS      [- missing AWS_ACCESS_KEY_ID]
  2. Azure    [- missing AZURE_STORAGE_CONNECTION_STRING]
  3. GCP      [+ ready]
  4. All configured providers

Select providers (comma-separated numbers, e.g. 1,3): 3
```

### Launch the Dashboard

```bash
streamlit run dashboard.py
```

> Run `benchmark.py` at least once first — the dashboard reads from `benchmark_results.csv`.

## Report Contents

The generated `benchmark_report_<timestamp>.txt` includes:

1. **Throughput Benchmark** — Upload/Download avg, min, max times and speeds (MB/s)
2. **Latency Benchmark** — Metadata, List, Delete latencies in milliseconds
3. **Head-to-Head Comparison** — Fastest/slowest for each operation
4. **Uploaded File URLs** — Direct links to files uploaded during benchmark
5. **Cost Estimation** — Monthly storage + egress costs for 1 TB (Singapore pricing)
6. **Vendor Lock-In Risk** — Qualitative analysis per provider
7. **Recommendations** — Data-driven suggestions

## API & Authentication Challenges

For a detailed analysis of the technical differences, authentication hurdles, and terminology variations between AWS, Azure, and GCP, see **[CHALLENGES.md](CHALLENGES.md)**.

## Quick Start (GCP Only)

```bash
pip install -r requirements.txt

# Edit .env — set GCP_PROJECT_ID and GCP_BUCKET_NAME
# Place gcp-key.json in this folder

python debug_env.py          # verify setup
python benchmark.py gcp      # run full benchmark
```

## Tech Stack

- **Python** — Core language
- **boto3** — AWS S3 SDK
- **azure-storage-blob** — Azure Blob Storage SDK
- **google-cloud-storage** — GCP Cloud Storage SDK
- **pandas** — Data analysis
- **Streamlit + Plotly** — Interactive dashboard
