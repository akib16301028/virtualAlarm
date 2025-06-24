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
        all_file = st.file_ploader("All Alarms", type=["xlsx", "xls"], key="all")  # Fixed typo: st.file_uploader

# Initialize session state for results
if 'results' not in st.session_state:
    st.session_state.results = []

def match_alarms(virtual_df, all_df):
    results = []
    virtual_df['Matched Nodes'] = ""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, row in virtual_df.iterrows():
        # Update progress - FIXED PARENTHESIS HERE
        progress = int((idx + 1) / len(virtual_df) * 100)  # Added closing parenthesis
        progress_bar.progress(progress)
        status_text.text(f"Processing {idx + 1}/{len(virtual_df)} alarms...")  # Fixed missing closing brace
        
        # Perform matching
        mask = (
            (all_df['Site Alias'] == row['Site Alias']) &
            (all_df['Start Time'] >= row['Start Time']) &
            (all_df['Start Time'] <= row['End Time'])
        )
        matches = all_df.loc[mask, 'Node'].unique()
        virtual_df.at[idx, 'Matched Nodes'] = ', '.join(matches)
        
        # Create result entry
        result_entry = {
            "Site Alias": row['Site Alias'],
            "Time Window": f"{row['Start Time']} to {row['End Time']}",
            "Matched Nodes": ', '.join(matches) if len(matches) > 0 else "No matches",
            "Match Count": len(matches)
        }
        st.session_state.results.append(result_entry)
        
        # Display immediately
        with st.container():
            cols = st.columns([1,2,3])
            cols[0].metric("Site", row['Site Alias'])
            cols[1].metric("Time Window", f"{row['Start Time']}\nto\n{row['End Time']}")
            cols[2].metric("Matches", f"{len(matches)} nodes", matches if len(matches) > 0 else "None")
            
            if len(matches) > 0:
                with st.expander(f"🔍 View {len(matches)} matched nodes"):
                    st.write(matches)
            
            st.markdown("---")  # Divider between entries
        
        time.sleep(0.3)  # Small delay for better visualization
    
    progress_bar.empty()
    status_text.empty()
    return virtual_df

# Main processing
if virtual_file and all_file:
    if st.button("🚀 Start Matching", type="primary"):
        st.session_state.results = []  # Clear previous results
        
        with st.spinner("Loading files..."):
            try:
                virtual_df = pd.read_excel(virtual_file)
                all_df = pd.read_excel(all_file)
                
                # Convert time columns
                time_cols = ['Start Time', 'End Time']
                for df in [virtual_df, all_df]:
                    for col in time_cols:
                        if col in df.columns:
                            df[col] = pd.to_datetime(df[col])
                
                # Display matching header
                st.subheader("🔎 Matching Results")
                result_df = match_alarms(virtual_df, all_df)
                
                # Show completion and download
                st.success("✅ All alarms processed!")
                
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    result_df.to_excel(writer, index=False)
                
                st.download_button(
                    label="📥 Download Full Results",
                    data=output.getvalue(),
                    file_name="Matched_Alarms.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
else:
    st.info("ℹ️ Please upload both files to begin")
