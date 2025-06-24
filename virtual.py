import streamlit as st
import pandas as pd
from io import BytesIO

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

# Matching function
def match_alarms(virtual_df, all_df):
    results = []
    virtual_df['Matched Nodes'] = ""
    
    for idx, row in virtual_df.iterrows():
        mask = (
            (all_df['Site Alias'] == row['Site Alias']) &
            (all_df['Start Time'] >= row['Start Time']) &
            (all_df['Start Time'] <= row['End Time'])
        )
        matches = all_df.loc[mask, 'Node'].unique()
        virtual_df.at[idx, 'Matched Nodes'] = ', '.join(matches)
        
        # Build progress output
        result_str = (
            f"**Site:** {row['Site Alias']} | "
            f"**Window:** {row['Start Time']} to {row['End Time']} | "
            f"**Matches:** {len(matches)} nodes"
        )
        results.append(result_str)
    
    return virtual_df, results

# Main processing
if virtual_file and all_file:
    if st.button("🚀 Find Matches", type="primary"):
        with st.spinner("Matching alarms..."):
            try:
                # Read files with datetime conversion
                virtual_df = pd.read_excel(virtual_file)
                all_df = pd.read_excel(all_file)
                
                # Convert time columns
                time_cols = ['Start Time', 'End Time']
                for df in [virtual_df, all_df]:
                    for col in time_cols:
                        if col in df.columns:
                            df[col] = pd.to_datetime(df[col])
                
                # Process data
                result_df, log_entries = match_alarms(virtual_df, all_df)
                
                # Show results
                st.success("✅ Matching complete!")
                
                with st.expander("📊 Results Preview", expanded=True):
                    st.dataframe(result_df.head())
                
                # Download button
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    result_df.to_excel(writer, index=False)
                
                st.download_button(
                    label="📥 Download Full Results",
                    data=output.getvalue(),
                    file_name="Matched_Alarms.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                # Show processing log
                with st.expander("📝 Matching Log"):
                    for entry in log_entries:
                        st.markdown(f"- {entry}")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
else:
    st.info("ℹ️ Please upload both files to begin")

# Instructions
with st.expander("ℹ️ HOW IT WORKS"):
    st.markdown("""
    **Matching Logic:**
    1. For each Virtual Alarm, finds All Alarms where:
       - `Site Alias` matches exactly
       - `Start Time` falls between the Virtual Alarm's time window
    2. Collects all matching Node names
    3. Outputs comma-separated matches
    
    **Required Columns:**
    - Both files need: `Site Alias`, `Node`, `Start Time`, `End Time`
    """)
