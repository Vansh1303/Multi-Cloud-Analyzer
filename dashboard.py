import streamlit as st
import pandas as pd
import plotly.express as px

# Set page configuration
st.set_page_config(page_title="Cloud Lock-In Analyzer", page_icon="☁️", layout="wide")

# Title and Description
st.title("☁️ Multi-Cloud Cost & Lock-In Analyzer")
st.markdown("""
This dashboard compares the **performance** and **lock-in risks** of major cloud providers.
Data is collected in real-time from your local machine to **Singapore (ap-southeast-1)** regions.
""")

# Load Data
try:
    df = pd.read_csv("benchmark_results.csv")
    df["Speed_MBps"] = pd.to_numeric(df["Speed_MBps"], errors='coerce')
    df["Time_Seconds"] = pd.to_numeric(df["Time_Seconds"], errors='coerce')
except FileNotFoundError:
    st.error("❌ No data found! Run 'python benchmark.py' first.")
    st.stop()
except Exception as e:
    st.error(f"❌ Error reading data: {e}")
    st.stop()

# Split into throughput (upload/download) and latency (metadata/list/delete)
speed_df = df[df["Speed_MBps"].notna()].copy()
latency_df = df[df["Operation"].isin(["Metadata", "List", "Delete"])].dropna(subset=["Time_Seconds"]).copy()

# --- KPI METRICS ---
st.subheader("🏆 Performance Overview")
col1, col2, col3 = st.columns(3)

avg_speeds = speed_df.groupby(["Provider", "Operation"])["Speed_MBps"].mean().unstack()

if not avg_speeds.empty:
    try:
        fastest_upload = avg_speeds["Upload"].idxmax()
        fastest_download = avg_speeds["Download"].idxmax()

        with col1:
            st.metric("Fastest Upload", fastest_upload, f"{avg_speeds.loc[fastest_upload, 'Upload']:.2f} MB/s")
        with col2:
            st.metric("Fastest Download", fastest_download, f"{avg_speeds.loc[fastest_download, 'Download']:.2f} MB/s")
        with col3:
            lock_in_risk = avg_speeds["Download"].idxmin()
            st.metric("Highest Lock-In Risk", lock_in_risk, "Slower Egress")
    except KeyError:
        st.warning("Not enough data to calculate metrics yet.")
else:
    st.warning("No valid speed data found.")

st.divider()

# --- THROUGHPUT CHARTS ---
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("🚀 Upload Speed Comparison")
    upload_df = speed_df[speed_df["Operation"] == "Upload"]
    if not upload_df.empty:
        fig_up = px.bar(
            upload_df, x="Provider", y="Speed_MBps", color="Provider",
            title="Upload Speed (MB/s) - Higher is Better", text_auto='.2f'
        )
        st.plotly_chart(fig_up, use_container_width=True)

with col_chart2:
    st.subheader("📥 Download Speed Comparison")
    download_df = speed_df[speed_df["Operation"] == "Download"]
    if not download_df.empty:
        fig_down = px.bar(
            download_df, x="Provider", y="Speed_MBps", color="Provider",
            title="Download Speed (MB/s) - Higher is Better", text_auto='.2f'
        )
        st.plotly_chart(fig_down, use_container_width=True)

# --- LATENCY CHARTS ---
if not latency_df.empty:
    st.divider()
    st.subheader("⚡ API Latency Comparison")

    # Convert to milliseconds for readability
    latency_df["Latency_ms"] = latency_df["Time_Seconds"] * 1000

    col_lat1, col_lat2, col_lat3 = st.columns(3)

    for col, op_name in zip([col_lat1, col_lat2, col_lat3], ["Metadata", "List", "Delete"]):
        with col:
            op_df = latency_df[latency_df["Operation"] == op_name]
            if not op_df.empty:
                fig = px.bar(
                    op_df, x="Provider", y="Latency_ms", color="Provider",
                    title=f"{op_name} Latency (ms) - Lower is Better", text_auto='.1f'
                )
                st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- COST ESTIMATION ---
st.subheader("💰 Estimated Monthly Cost (1 TB Storage)")
st.info("Based on standard Singapore region pricing (approximate).")

pricing = {
    "AWS": {"storage": 0.025, "egress": 0.09},
    "Azure": {"storage": 0.020, "egress": 0.087},
    "GCP": {"storage": 0.023, "egress": 0.12}
}

cost_data = []
unique_providers = df["Provider"].unique()

for provider in unique_providers:
    if provider in pricing:
        storage_cost = 1000 * pricing[provider]["storage"]  # 1TB
        egress_cost = 1000 * pricing[provider]["egress"]    # Moving 1TB out
        cost_data.append({
            "Provider": provider,
            "Storage Cost ($)": storage_cost,
            "Egress (Exit) Cost ($)": egress_cost
        })

if cost_data:
    df_cost = pd.DataFrame(cost_data)
    format_mapping = {"Storage Cost ($)": "${:.2f}", "Egress (Exit) Cost ($)": "${:.2f}"}
    st.dataframe(
        df_cost.style.format(format_mapping),
        use_container_width=True
    )

# --- RAW DATA ---
with st.expander("View Raw Benchmark Logs"):
    st.dataframe(df)
