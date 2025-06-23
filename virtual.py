import streamlit as st
import pandas as pd
import io

st.title("⚡ Virtual Alarm Matcher")

# File uploaders
virtual_file = st.file_uploader("Upload Virtual Alarm File (.xlsx, .xls, .csv)", type=["xlsx", "xls", "csv"])
all_file = st.file_uploader("Upload All Alarm File (.xlsx, .xls, .csv)", type=["xlsx", "xls", "csv"])

required_cols = ["Rms Station", "Site Alias", "Zone", "Node", "Cluster", "Tenant", "Start Time", "End Time"]

# Function to read Excel or CSV
def read_file(file):
    if file.name.endswith((".xlsx", ".xls")):
        return pd.read_excel(file)
    elif file.name.endswith(".csv"):
        return pd.read_csv(file)
    else:
        return None

# Function to validate required columns
def validate_columns(df, name):
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        st.error(f"{name} is missing columns: {', '.join(missing)}")
        return False
    return True

# Main logic
if virtual_file and all_file:
    df_virtual = read_file(virtual_file)
    df_all = read_file(all_file)

    if df_virtual is not None and df_all is not None:
        # Convert to datetime
        try:
            df_virtual["Start Time"] = pd.to_datetime(df_virtual["Start Time"])
            df_virtual["End Time"] = pd.to_datetime(df_virtual["End Time"])
            df_all["Start Time"] = pd.to_datetime(df_all["Start Time"])
        except Exception as e:
            st.error(f"Date conversion error: {e}")
            st.stop()

        if validate_columns(df_virtual, "Virtual Alarm") and validate_columns(df_all, "All Alarm"):
            # Merge on Site Alias
            merged = df_virtual.merge(df_all, on="Site Alias", suffixes=('_v', '_a'))

            # Filter rows where All Alarm's Start Time falls within Virtual Alarm's time window
            filtered = merged[
                (merged["Start Time_a"] >= merged["Start Time_v"]) &
                (merged["Start Time_a"] <= merged["End Time_v"])
            ]

            # Create a key to map back to Virtual Alarm rows
            filtered["match_key"] = (
                filtered["Site Alias"] + "|" +
                filtered["Start Time_v"].astype(str) + "|" +
                filtered["End Time_v"].astype(str)
            )

            # Group matched Nodes
            node_group = filtered.groupby("match_key")["Node_a"].apply(lambda x: ", ".join(x.dropna().unique()))

            # Create same key in original virtual
            df_virtual["match_key"] = (
                df_virtual["Site Alias"] + "|" +
                df_virtual["Start Time"].astype(str) + "|" +
                df_virtual["End Time"].astype(str)
            )

            # Map the nodes
            df_virtual["Matched Nodes from All Alarm"] = df_virtual["match_key"].map(node_group).fillna("")
            df_virtual.drop(columns="match_key", inplace=True)

            # Save to Excel in memory
            output = io.BytesIO()
            df_virtual.to_excel(output, index=False, engine="openpyxl")

            # Download button
            st.download_button(
                label="📥 Download Result Excel",
                data=output.getvalue(),
                file_name="matched_virtual_alarms.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        else:
            st.stop()
    else:
        st.error("Could not read one or both files.")
