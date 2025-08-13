import streamlit as st
from utils import extract_pdf_blocks
import tempfile
import json
import pandas as pd
import os

st.set_page_config(page_title="Voter Data Extraction", page_icon=":guardsman:", layout="wide")
st.title("Voter Data Extraction")

# Initialize session state
if 'voter_data' not in st.session_state:
    st.session_state.voter_data = None
if 'processed_file' not in st.session_state:
    st.session_state.processed_file = None

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file is not None:
    # Check if this is a new file
    if st.session_state.processed_file != uploaded_file.name:
        st.session_state.processed_file = uploaded_file.name
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_file_path = tmp_file.name
        
        try:
            with st.spinner("Extracting voter data from PDF..."):
                voter_list = extract_pdf_blocks(tmp_file_path)
                st.session_state.voter_data = voter_list
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")
            st.session_state.voter_data = None
        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    # Display data if available
    if st.session_state.voter_data:
        voter_list = st.session_state.voter_data
        df = pd.DataFrame(voter_list)
        
        st.success(f"Successfully extracted {len(voter_list)} voter records")
        st.dataframe(df.head(10))
        
        # Download buttons
        col1, space1, space2, space3, col2= st.columns(5)
        
        with col1:
            json_data = json.dumps(voter_list, indent=4)
            st.download_button(
                label="📄 Download JSON",
                data=json_data,
                file_name="voter_data.json",
                mime="application/json",
                key="json_download",
                use_container_width=True
            )
        
        with col2:
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📊 Download CSV",
                data=csv_data,
                file_name="voter_data.csv",
                mime="text/csv",
                key="csv_download",
                use_container_width=True
            )
       
    else:
        st.warning("No voter data found in the PDF")