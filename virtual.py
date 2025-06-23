import streamlit as st
import pandas as pd
from datetime import datetime
import io

st.set_page_config(page_title="Alarm Matcher", layout="wide")

st.title("Alarm Matching Tool")
st.write("Upload your Virtual Alarms and All Alarms files to find matching nodes")

# File upload section
col1, col2 = st.columns(2)

with col1:
    st.subheader("Virtual Alarms File")
    virtual_file = st.file_uploader("Upload Virtual Alarms Excel file", type=["xlsx", "xls"], key="virtual")

with col2:
    st.subheader("All Alarms File")
    all_file = st.file_uploader("Upload All Alarms Excel file", type=["xlsx", "xls"], key="all")

def process_alarms(virtual_df, all_df):
    # Convert time columns to datetime if they're not already
    time_columns = ['Start Time', 'End Time']
    for df in [virtual_df, all_df]:
        for col in time_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])

    # Create a new column for matched nodes
    virtual_df['Matched Nodes'] = ''

    # Process each virtual alarm
    for idx, v_row in virtual_df.iterrows():
        site_alias = v_row['Site Alias']
        v_start = v_row['Start Time']
        v_end = v_row['End Time']

        # Find matching alarms in all alarms file
        matches = all_df[
            (all_df['Site Alias'] == site_alias) &
            (all_df['Start Time'] >= v_start) &
            (all_df['Start Time'] <= v_end)
        ]

        # Get unique node names and join them
        matched_nodes = matches['Node'].dropna().unique()
        virtual_df.at[idx, 'Matched Nodes'] = ', '.join(matched_nodes)

    return virtual_df

if virtual_file and all_file:
    try:
        # Read the uploaded files
        virtual_df = pd.read_excel(virtual_file)
        all_df = pd.read_excel(all_file)

        # Check if required columns exist
        required_columns = ['Site Alias', 'Start Time', 'End Time', 'Node']
        for col in required_columns:
            if col not in virtual_df.columns or col not in all_df.columns:
                st.error(f"Both files must contain '{col}' column")
                st.stop()

        # Show preview of uploaded files
        st.subheader("File Previews")
        tab1, tab2 = st.tabs(["Virtual Alarms Preview", "All Alarms Preview"])
        
        with tab1:
            st.write("First 5 rows of Virtual Alarms:")
            st.dataframe(virtual_df.head())
        
        with tab2:
            st.write("First 5 rows of All Alarms:")
            st.dataframe(all_df.head())

        # Process files when button is clicked
        if st.button("Process Alarms", type="primary"):
            with st.spinner("Processing alarms..."):
                result_df = process_alarms(virtual_df.copy(), all_df.copy())
            
            st.success("Processing complete!")
            
            # Show results
            st.subheader("Results")
            st.dataframe(result_df)
            
            # Download button
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                result_df.to_excel(writer, index=False)
            output.seek(0)
            
            st.download_button(
                label="Download Results",
                data=output,
                file_name="Virtual_Alarms_With_Matches.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
else:
    st.info("Please upload both files to proceed")
