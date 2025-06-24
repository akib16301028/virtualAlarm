import streamlit as st
import pandas as pd
from io import BytesIO
import time
import gc  # For memory management

st.set_page_config(page_title="Alarm Matcher", layout="centered")
st.title("🔔 Batch Alarm Matching Tool")

# Constants
BATCH_SIZE = 100  # Adjust based on your system's memory
MAX_LOG_LINES = 20  # Keep log manageable

with st.expander("📁 Upload Alarm Files", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        virtual_file = st.file_uploader("Virtual Alarms", type=["xlsx", "xls"], key="virtual")
    with col2:
        all_file = st.file_uploader("All Alarms", type=["xlsx", "xls"], key="all")

# Function to match one batch with better memory management
def match_batch(virtual_df, all_df, start_index, end_index, progress_log):
    batch_results = []
    for idx in range(start_index, end_index):
        row = virtual_df.iloc[idx]
        try:
            mask = (
                (all_df['Site Alias'] == row['Site Alias']) &
                (all_df['Start Time'] >= row['Start Time']) &
                (all_df['Start Time'] <= row['End Time'])
            )
            matched_nodes = all_df.loc[mask, 'Node'].unique()
            result = ', '.join(matched_nodes)
            
            # Add live log
            log_line = f"✅ {idx+1}/{len(virtual_df)} - `{row['Site Alias']}` ➜ {len(matched_nodes)} node(s)"
            progress_log.append(log_line)
            batch_results.append(result)
            
            # Clear memory periodically
            if idx % 10 == 0:
                gc.collect()
                
        except Exception as e:
            progress_log.append(f"❌ Error processing row {idx+1}: {str(e)}")
            batch_results.append("")
            
    return batch_results

if virtual_file and all_file:
    if st.button("🚀 Start Matching", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        log_display = st.empty()
        download_sections = st.container()
        
        try:
            # Read files with explicit dtype specification
            virtual_df = pd.read_excel(virtual_file)
            all_df = pd.read_excel(all_file)

            # Convert datetime columns with error handling
            for df in [virtual_df, all_df]:
                for col in ['Start Time', 'End Time']:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                    else:
                        raise ValueError(f"Column '{col}' not found in DataFrame")

            # Initialize results
            virtual_df['Matched Nodes'] = ""
            total_rows = len(virtual_df)
            progress_log = []
            
            # Process in batches with better progress tracking
            for batch_start in range(0, total_rows, BATCH_SIZE):
                batch_end = min(batch_start + BATCH_SIZE, total_rows)
                status_text.text(f"Processing rows {batch_start+1} to {batch_end} of {total_rows}")
                
                # Process batch
                batch_results = match_batch(virtual_df, all_df, batch_start, batch_end, progress_log)
                virtual_df.loc[batch_start:batch_end-1, 'Matched Nodes'] = batch_results
                
                # Update progress
                progress = min((batch_end) / total_rows, 1.0)
                progress_bar.progress(progress)
                
                # Update log (show last MAX_LOG_LINES only)
                log_display.code("\n".join(progress_log[-MAX_LOG_LINES:]), language="markdown")
                
                # Show partial download
                with download_sections.expander(f"📄 Partial Results (Rows 1-{batch_end})", expanded=False):
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        virtual_df.iloc[:batch_end].to_excel(writer, index=False)
                    st.download_button(
                        label=f"📥 Download Rows 1–{batch_end}",
                        data=output.getvalue(),
                        file_name=f"Matched_Alarms_1_to_{batch_end}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"download_{batch_end}"  # Unique key for each button
                    )
                
                # Force Streamlit to update the UI
                st.experimental_rerun()
                time.sleep(0.1)  # Small delay to allow UI updates

            # Final download
            st.success("✅ Full Matching Complete!")
            with st.expander("📦 Download Full Result File", expanded=True):
                final_output = BytesIO()
                with pd.ExcelWriter(final_output, engine='xlsxwriter') as writer:
                    virtual_df.to_excel(writer, index=False)
                st.download_button(
                    label="📥 Download Complete File",
                    data=final_output.getvalue(),
                    file_name="Matched_Alarms_Full.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="final_download"
                )

        except Exception as e:
            st.error(f"❌ Critical Error: {str(e)}")
            st.exception(e)  # Show full traceback for debugging
else:
    st.info("📝 Please upload both files first to begin.")

with st.expander("ℹ️ How It Works"):
    st.markdown("""
    - Matches `Site Alias` where `Start Time` of All Alarms falls between Virtual Alarm window
    - Processes in batches of 100 rows for better memory management
    - Shows real-time progress and allows partial downloads
    - Includes error handling and memory cleanup
    """)
