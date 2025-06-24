import streamlit as st
import pandas as pd
from io import BytesIO
import time

# App setup
st.set_page_config(page_title="Alarm Matcher", layout="centered")
st.title("🔔 Alarm Matching Tool")

# File upload section
with st.expander("📁 UPLOAD FILES", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        virtual_file = st.file_uploader("Virtual Alarms", type=["xlsx", "xls"], key="virtual")
    with col2:
        all_file = st.file_uploader("All Alarms", type=["xlsx", "xls"], key="all")

# Matching function with per-row feedback
def match_alarms_live(virtual_df, all_df):
    result_df = virtual_df.copy()
    result_df['Matched Nodes'] = ""

    log_placeholder = st.empty()
    logs = []

    for idx, row in result_df.iterrows():
        mask = (
            (all_df['Site Alias'] == row['Site Alias']) &
            (all_df['Start Time'] >= row['Start Time']) &
            (all_df['Start Time'] <= row['End Time'])
        )
        matched_nodes = all_df.loc[mask, 'Node'].unique()
        result_df.at[idx, 'Matched Nodes'] = ', '.join(matched_nodes)

        # Display log live
        log_line = (
            f"✅ **{idx+1}/{len(result_df)} - Site:** `{row['Site Alias']}` | "
            f"**Window:** {row['Start Time']} → {row['End Time']} | "
            f"**Matches:** {len(matched_nodes)}"
        )
        logs.append(f"- {log_line}")
        log_placeholder.markdown("\n".join(logs))
        time.sleep(0.05)  # Optional: slight delay for better visual

    return result_df

# Main processing
if virtual_file and all_file:
    if st.button("🚀 Start Matching", type="primary"):
        with st.spinner("Processing alarm matches..."):
            try:
                # Read files
                virtual_df = pd.read_excel(virtual_file)
                all_df = pd.read_excel(all_file)

                # Ensure time columns are datetime
                time_cols = ['Start Time', 'End Time']
                for df in [virtual_df, all_df]:
                    for col in time_cols:
                        if col in df.columns:
                            df[col] = pd.to_datetime(df[col])

                # Start live matching
                st.subheader("🔎 Matching Progress")
                matched_df = match_alarms_live(virtual_df, all_df)

                # Show final results
                st.success("✅ Matching complete!")
                with st.expander("📊 Preview First Few Rows", expanded=True):
                    st.dataframe(matched_df.head())

                # Prepare downloadable output
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    matched_df.to_excel(writer, index=False)

                st.download_button(
                    label="📥 Download Full Results Excel",
                    data=output.getvalue(),
                    file_name="Matched_Alarms.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            except Exception as e:
                st.error(f"❌ Error occurred: {str(e)}")
else:
    st.info("📂 Please upload both Virtual and All Alarm Excel files to begin.")

# Instruction section
with st.expander("ℹ️ How It Works"):
    st.markdown("""
    **🔍 Matching Logic:**
    - For each **Virtual Alarm**:
      - Matches any **All Alarm** where:
        - `Site Alias` is the same
        - `Start Time` falls between `Start` and `End Time` of virtual alarm
      - Extracts and lists matched `Node` values

    **✅ Required Columns:**
    - Both files should contain:
      - `Site Alias`, `Node`, `Start Time`, `End Time`
    """)
