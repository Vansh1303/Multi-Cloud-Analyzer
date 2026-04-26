"""
Multi-Cloud Cost & Lock-In Analyzer — FastAPI Middleware
========================================================
Endpoints:
    GET  /api/telemetry  — Returns benchmark telemetry as structured JSON
    POST /api/run        — Triggers a benchmark run (Firebase JWT-protected)

Author: Vansh Jha
"""

import os
import subprocess
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

import firebase_admin
from firebase_admin import auth, credentials

# ─────────────────────────────────────────────
# ENV & PATHS
# ─────────────────────────────────────────────
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "benchmark_results.csv"
FIREBASE_KEY = BASE_DIR / "firebase-admin-key.json"

# ─────────────────────────────────────────────
# FIREBASE ADMIN SDK INITIALIZATION
# ─────────────────────────────────────────────
if FIREBASE_KEY.exists():
    cred = credentials.Certificate(str(FIREBASE_KEY))
    firebase_admin.initialize_app(cred)
    print("[OK] Firebase Admin SDK initialized.")
else:
    print("[WARN] firebase-admin-key.json not found -- JWT verification will fail.")
    # Initialize without credentials so the app still starts for development
    try:
        firebase_admin.initialize_app()
    except ValueError:
        pass  # Already initialized

# ─────────────────────────────────────────────
# FASTAPI APP
# ─────────────────────────────────────────────
app = FastAPI(
    title="Multi-Cloud Analyzer API",
    description="Middleware for the Multi-Cloud Cost & Lock-In Analyzer mobile app.",
    version="1.0.0",
)

# CORS — allow all origins during development, lock down for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# PRICING TABLE (matches dashboard.py)
# ─────────────────────────────────────────────
PRICING = {
    "AWS":   {"storage_per_gb": 0.023, "egress_per_gb": 0.09},
    "Azure": {"storage_per_gb": 0.020, "egress_per_gb": 0.087},
    "GCP":   {"storage_per_gb": 0.023, "egress_per_gb": 0.12},
}


# ─────────────────────────────────────────────
# MOCK DATA GENERATOR (failsafe)
# ─────────────────────────────────────────────
def _generate_mock_telemetry() -> dict:
    """
    Returns structured mock telemetry matching the master spec.
    Used when benchmark_results.csv is missing or empty.
    """
    return {
        "source": "mock",
        "providers": ["AWS", "Azure", "GCP"],
        "upload_speeds": {
            "AWS":   6.34,
            "Azure": 2.89,
            "GCP":   9.25,
        },
        "download_speeds": {
            "AWS":   7.02,
            "Azure": 3.94,
            "GCP":   9.86,
        },
        "latency_ms": {
            "AWS":   {"Metadata": 65.9,  "List": 72.7,   "Delete": 93.7},
            "Azure": {"Metadata": 64.2,  "List": 68.3,   "Delete": 64.4},
            "GCP":   {"Metadata": 107.2, "List": 7284.0, "Delete": 102.9},
        },
        "cost_estimate": {
            "AWS":   {"storage": 23.0,  "egress": 90.0},
            "Azure": {"storage": 20.0,  "egress": 87.0},
            "GCP":   {"storage": 23.0,  "egress": 120.0},
        },
        "portability": [
            {"route": "AWS->Azure",  "time_seconds": 35.16},
            {"route": "AWS->GCP",    "time_seconds": 15.89},
            {"route": "Azure->AWS",  "time_seconds": 26.34},
            {"route": "Azure->GCP",  "time_seconds": 25.68},
            {"route": "GCP->AWS",    "time_seconds": 16.69},
            {"route": "GCP->Azure",  "time_seconds": 28.76},
        ],
    }


# ─────────────────────────────────────────────
# CSV → STRUCTURED JSON PARSER
# ─────────────────────────────────────────────
def _parse_csv_to_telemetry() -> dict:
    """
    Reads benchmark_results.csv and returns the structured JSON payload.
    CSV columns: Provider, Operation, Time_Seconds, Speed_MBps,
                 Size_MB, Round, URL, Timestamp
    """
    if not CSV_FILE.exists():
        return _generate_mock_telemetry()

    try:
        df = pd.read_csv(
            CSV_FILE,
            header=None,
            names=[
                "Provider", "Operation", "Time_Seconds",
                "Speed_MBps", "Size_MB", "Round", "URL", "Timestamp",
            ],
        )
    except Exception:
        return _generate_mock_telemetry()

    if df.empty:
        return _generate_mock_telemetry()

    df["Speed_MBps"] = pd.to_numeric(df["Speed_MBps"], errors="coerce")
    df["Time_Seconds"] = pd.to_numeric(df["Time_Seconds"], errors="coerce")

    # Filter out portability routes for core metrics
    core_providers = [p for p in df["Provider"].unique() if "->" not in p]

    # ── Upload / Download Speeds (avg MB/s per provider) ──
    speed_df = df[df["Speed_MBps"].notna()]
    upload_speeds = (
        speed_df[speed_df["Operation"] == "Upload"]
        .groupby("Provider")["Speed_MBps"]
        .mean()
        .to_dict()
    )
    download_speeds = (
        speed_df[speed_df["Operation"] == "Download"]
        .groupby("Provider")["Speed_MBps"]
        .mean()
        .to_dict()
    )

    # Round to 2 decimal places
    upload_speeds = {k: round(v, 2) for k, v in upload_speeds.items()}
    download_speeds = {k: round(v, 2) for k, v in download_speeds.items()}

    # ── API Latency (avg ms per provider × operation) ──
    latency_ops = df[df["Operation"].isin(["Metadata", "List", "Delete"])]
    latency_ms: dict[str, dict[str, float]] = {}
    for provider in core_providers:
        prov_df = latency_ops[latency_ops["Provider"] == provider]
        latency_ms[provider] = {
            op: round(
                prov_df[prov_df["Operation"] == op]["Time_Seconds"].mean() * 1000, 1
            )
            for op in ["Metadata", "List", "Delete"]
            if not prov_df[prov_df["Operation"] == op].empty
        }

    # ── Cost Estimate (1 TB = 1000 GB) ──
    cost_estimate: dict[str, dict[str, float]] = {}
    for provider in core_providers:
        if provider in PRICING:
            p = PRICING[provider]
            cost_estimate[provider] = {
                "storage": round(1000 * p["storage_per_gb"], 2),
                "egress": round(1000 * p["egress_per_gb"], 2),
            }

    # ── Portability Routes ──
    port_df = df[df["Operation"] == "Portability"]
    portability = [
        {
            "route": row["Provider"],
            "time_seconds": round(row["Time_Seconds"], 2),
        }
        for _, row in port_df.iterrows()
    ]

    return {
        "source": "csv",
        "providers": sorted(core_providers),
        "upload_speeds": upload_speeds,
        "download_speeds": download_speeds,
        "latency_ms": latency_ms,
        "cost_estimate": cost_estimate,
        "portability": portability,
    }


# ─────────────────────────────────────────────
# HELPER — Verify Firebase JWT
# ─────────────────────────────────────────────
def _verify_firebase_token(request: Request) -> dict:
    """
    Extracts the Bearer token from the Authorization header
    and verifies it using Firebase Admin SDK.
    Returns the decoded token claims on success.
    Raises HTTPException 401 on failure.
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or malformed Authorization header. Expected: Bearer <token>",
        )

    token = auth_header.split("Bearer ")[1]

    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except firebase_admin.exceptions.FirebaseError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid or expired Firebase token: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Token verification failed: {str(e)}",
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENDPOINTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@app.get("/")
async def root():
    """Health check / welcome endpoint."""
    return {
        "service": "Multi-Cloud Analyzer API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "telemetry": "GET  /api/telemetry",
            "run":       "POST /api/run",
            "docs":      "GET  /docs",
        },
    }


@app.get("/api/telemetry")
async def get_telemetry():
    """
    Returns the full benchmark telemetry as structured JSON.
    Reads from benchmark_results.csv if available, otherwise
    falls back to mock data.
    """
    telemetry = _parse_csv_to_telemetry()
    return telemetry


@app.post("/api/run")
async def run_benchmark(request: Request):
    """
    Triggers a benchmark run. Protected by Firebase JWT.

    Flow:
    1. Extract & verify the Firebase Bearer token
    2. Execute the benchmark engine (Docker subprocess)
    3. Return the run status
    """
    # Step 1: Verify Firebase JWT
    decoded_token = _verify_firebase_token(request)
    uid = decoded_token.get("uid", "unknown")
    email = decoded_token.get("email", "unknown")

    # Step 2: Trigger the benchmark engine
    try:
        result = subprocess.run(
            ["python", "benchmark.py", "aws,azure,gcp"],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(BASE_DIR),
        )
        if result.returncode == 0:
            return {
                "status": "success",
                "message": "Benchmark run completed successfully.",
                "triggered_by": {"uid": uid, "email": email},
                "output": result.stdout
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Benchmark failed: {result.stderr}"
            )
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="Benchmark timed out after 300 seconds."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute benchmark: {str(e)}"
        )


# ─────────────────────────────────────────────
# ENTRYPOINT (for direct execution)
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
