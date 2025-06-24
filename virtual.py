import streamlit as st
import pandas as pd
from io import BytesIO
import time

st.set_page_config(page_title="Alarm Matcher", layout="centered")
st.title("🔔 Batch Alarm Matching Tool")

with st.expander("📁 Upload Alarm Files", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        virtual_file = st.file_uploader("Virtual Alarms", type=["xlsx", "xls"], key="virtual")
    with col2:
        all_file = st.file_uploader("All Alarms", type=["xlsx", "xls"], key="all")

BATCH_SIZE = 100  # You can adjust this

# Function to match one batch
def match_batch(virtual_df, all_df, start_index, end_index, progress_log):
    for idx in range(start_index, end_index):
        row = virtual_df.iloc[idx]
        mask = (
            (all_df['Site Alias'] == row['Site Alias']) &
            (all_df['Start Time'] >= row['Start Time']) &
            (all_df['Start Time'] <= row['End Time'])
        )
        matched_nodes = all_df.loc[mask, 'Node'].unique()
        virtual_df.at[idx, 'Matched Nodes'] = ', '.join(matched_nodes)

        # Add live log
        log_line = f"✅ {idx+1}/{len(virtual_df)} - `{row['Site Alias']}` ➜ {len(matched_nodes)} node(s)"
        progress_log.append(f"- {log_line}")
    return virtual_df

if virtual_file and all_file:
    if st.button("🚀 Start Matching", type="primary"):
        try:
            virtual_df = pd.read_excel(virtual_file)
            all_df = pd.read_excel(all_file)

            # Convert datetime columns
            for df in [virtual_df, all_df]:
                for col in ['Start Time', 'End Time']:
                    df[col] = pd.to_datetime(df[col])

            # Prepare output column
            virtual_df['Matched Nodes'] = ""
            total_rows = len(virtual_df)
            progress_log = []
            log_display = st.empty()
            download_sections = []

            # Process in batches
            for batch_start in range(0, total_rows, BATCH_SIZE):
                batch_end = min(batch_start + BATCH_SIZE, total_rows)
                virtual_df = match_batch(virtual_df, all_df, batch_start, batch_end, progress_log)

                # Update log
                log_display.markdown("\n".join(progress_log[-10:]))  # show last 10 logs only for brevity
                time.sleep(0.5)  # for better effect (optional)

                # Show partial download
                part_df = virtual_df.iloc[:batch_end]
                with st.expander(f"📄 Download Results Up to Row {batch_end}"):
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        part_df.to_excel(writer, index=False)
                    st.download_button(
                        label=f"📥 Download Batch 1–{batch_end}",
                        data=output.getvalue(),
                        file_name=f"Matched_Alarms_1_to_{batch_end}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

            st.success("✅ Full Matching Complete!")

            # Final download
            with st.expander("📦 Download Full Result File"):
                final_output = BytesIO()
                with pd.ExcelWriter(final_output, engine='xlsxwriter') as writer:
                    virtual_df.to_excel(writer, index=False)
                st.download_button(
                    label="📥 Download Complete File",
                    data=final_output.getvalue(),
                    file_name="Matched_Alarms_Full.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
else:
    st.info("📝 Please upload both files first to begin.")

with st.expander("ℹ️ How It Works"):
    st.markdown("""
    - Matches `Site Alias` where `Start Time` of All Alarms falls between Virtual Alarm window.
    - Each batch processes 100 rows.
    - You can download partial results after each batch.
    """)
