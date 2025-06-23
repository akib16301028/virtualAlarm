import streamlit as st
import pandas as pd
from datetime import datetime
import io

st.set_page_config(page_title="Alarm Matcher", layout="wide")
st.title("Alarm Matching Tool")

# File upload section
virtual_file = st.file_uploader("Upload Virtual Alarms", type=["xlsx", "xls"])
all_file = st.file_uploader("Upload All Alarms", type=["xlsx", "xls"])

def process_alarms(virtual_df, all_df):
    virtual_df['Matched Nodes'] = ''
    results = []
    
    for idx, v_row in virtual_df.iterrows():
        matches = all_df[
            (all_df['Site Alias'] == v_row['Site Alias']) &
            (all_df['Start Time'] >= v_row['Start Time']) &
            (all_df['Start Time'] <= v_row['End Time'])
        ]
        
        matched_nodes = ', '.join(matches['Node'].dropna().unique())
        virtual_df.at[idx, 'Matched Nodes'] = matched_nodes
        
        # Display each row result immediately
        result_str = f"• Site {v_row['Site Alias']} ({v_row['Start Time']} to {v_row['End Time']}): {matched_nodes or 'No matches'}"
        results.append(result_str)
        st.write(result_str)
    
    return virtual_df, results

if virtual_file and all_file:
    if st.button("Process Alarms", type="primary"):
        virtual_df = pd.read_excel(virtual_file)
        all_df = pd.read_excel(all_file)
        
        # Convert time columns
        for df in [virtual_df, all_df]:
            df['Start Time'] = pd.to_datetime(df['Start Time'])
            df['End Time'] = pd.to_datetime(df['End Time'])
        
        # Process and show row-by-row output
        st.subheader("Processing Results:")
        result_df, _ = process_alarms(virtual_df, all_df)
        
        # Show completion message and download
        st.success("✅ All rows processed!")
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            result_df.to_excel(writer, index=False)
        
        st.download_button(
            label="Download Full Results",
            data=output.getvalue(),
            file_name="Matched_Alarms.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Please upload both files to begin")
