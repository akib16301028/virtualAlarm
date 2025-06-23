import streamlit as st
import pandas as pd
import io

st.title("📁 Step 1: Upload Alarm Files (Excel or CSV)")

# File uploader
virtual_file = st.file_uploader("Upload Virtual Alarm File", type=["xlsx", "xls", "csv"], key="virtual")
all_file = st.file_uploader("Upload All Alarm File", type=["xlsx", "xls", "csv"], key="all")

# Required columns
required_columns = [
    "Rms Station", "Site Alias", "Zone", "Node",
    "Cluster", "Tenant", "Start Time", "End Time"
]

# File reading function
def read_alarm_file(uploaded_file):
    try:
        if uploaded_file.name.endswith((".xlsx", ".xls")):
            return pd.read_excel(uploaded_file)
        elif uploaded_file.name.endswith(".csv"):
            return pd.read_csv(uploaded_file)
        else:
            st.warning("Unsupported file type. Please upload .xlsx, .xls, or .csv")
            return None
    except Exception as e:
        st.error(f"Error reading file {uploaded_file.name}: {e}")
        return None

# Column validator
def validate_columns(df, file_name):
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        st.error(f"❌ {file_name} is missing columns: {', '.join(missing)}")
        return False
    return True

# Load and validate files
if virtual_file and all_file:
    df_virtual = read_alarm_file(virtual_file)
    df_all = read_alarm_file(all_file)

    if df_virtual is not None and df_all is not None:
        # Show file previews
        with st.expander("🔍 Preview: Virtual Alarm"):
            st.dataframe(df_virtual)

        with st.expander("🔍 Preview: All Alarm"):
            st.dataframe(df_all)

        # Validate
        if validate_columns(df_virtual, "Virtual Alarm") and validate_columns(df_all, "All Alarm"):
            st.success("✅ Both files uploaded and verified successfully.")
        else:
            st.stop()
else:
    st.info("⬆ Please upload both files (Excel or CSV) to continue.")
