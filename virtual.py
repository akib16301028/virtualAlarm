import streamlit as st
import pandas as pd
import io

st.title("⚡ Virtual Alarm Node Matcher")

# Upload files
virtual_file = st.file_uploader("Upload Virtual Alarm File (.xlsx, .xls, .csv)", type=["xlsx", "xls", "csv"])
all_file = st.file_uploader("Upload All Alarm File (.xlsx, .xls, .csv)", type=["xlsx", "xls", "csv"])

# Required columns
required_cols = ["Rms Station", "Site Alias", "Zone", "Node", "Cluster", "Tenant", "Start Time", "End Time"]

# Read function
def read_file(file):
    if file.name.endswith((".xlsx", ".xls")):
        return pd.read_excel(file)
    elif file.name.endswith(".csv"):
        return pd.read_csv(file)
    return None

# Validate required columns
def validate_columns(df, name):
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        st.error(f"{name} file is missing columns: {', '.join(missing)}")
        return False
    return True

# Main matching logic
if virtual_file and all_file:
    df_virtual = read_file(virtual_file)
    df_all = read_file(all_file)

    if df_virtual is not None and df_all is not None:
        # Validate columns
        if not validate_columns(df_virtual, "Virtual Alarm") or not validate_columns(df_all, "All Alarm"):
            st.stop()

        try:
            # Ensure datetime
            df_virtual["Start Time"] = pd.to_datetime(df_virtual["Start Time"])
            df_virtual["End Time"] = pd.to_datetime(df_virtual["End Time"])
            df_all["Start Time"] = pd.to_datetime(df_all["Start Time"])
        except Exception as e:
            st.error(f"Date conversion failed: {e}")
            st.stop()

        # Create unique keys for grouping
        df_virtual["match_key"] = (
            df_virtual["Site Alias"].astype(str) + "|" +
            df_virtual["Start Time"].astype(str) + "|" +
            df_virtual["End Time"].astype(str)
        )

        # Merge and filter
        merged = df_virtual.merge(df_all, on="Site Alias", suffixes=('_v', '_a'))
        matched = merged[
            (merged["Start Time_a"] >= merged["Start Time_v"]) &
            (merged["Start Time_a"] <= merged["End Time_v"])
        ]

        # Group matched nodes
        matched["group_key"] = (
            matched["Site Alias"] + "|" +
            matched["Start Time_v"].astype(str) + "|" +
            matched["End Time_v"].astype(str)
        )
        node_map = matched.groupby("group_key")["Node_a"].apply(lambda x: ", ".join(x.dropna().unique()))

        # Add matched nodes to virtual dataframe
        df_virtual["Matched Nodes from All Alarm"] = df_virtual["match_key"].map(node_map).fillna("")
        df_virtual.drop(columns=["match_key"], inplace=True)

        # Download as Excel
        output = io.BytesIO()
        df_virtual.to_excel(output, index=False, engine="openpyxl")
        st.download_button(
            label="📥 Download Matched Excel",
            data=output.getvalue(),
            file_name="matched_virtual_alarm.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("Failed to read one or both files.")
else:
    st.info("📂 Please upload both files to continue.")
