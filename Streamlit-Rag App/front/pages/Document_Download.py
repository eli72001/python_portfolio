import streamlit as st
import os
import time
import base64
from datetime import datetime
from OutputParser import OutputParser
from RagApplication import RagApplication
from pathlib import Path
import io
import glob

from frontendhelper import clean_path, show_pdf, get_filename

# st.image(r'ui_assets\Kubrick_Logo_DarkGreen.png', width=100)
st.title('Document Download Center')
st.markdown("You can find all the annotated PDFs from your query session here.")
st.divider()

annotated_docs = 'annotated_docs'

widget_id = (id for id in range(1, 100_00))
if os.listdir(annotated_docs):
    for dir in Path(annotated_docs).iterdir():
        for annotated_doc in os.listdir(dir):
            anno_doc_name = os.path.basename(annotated_doc)
            anno_doc_time = time.ctime(os.path.getmtime(os.path.join(dir, annotated_doc)))
            with st.container():
                name, mod_date, preview, download = st.columns((1.5,2.3,1,1))
                with name:
                    st.markdown(f'**Annotated_{anno_doc_name}**', unsafe_allow_html=True)    
                with mod_date: 
                    st.markdown(f"Last modified: {anno_doc_time}")
                with preview:
                    with st.popover('Preview PDF'):    # can replace with st.popover if just want popup preview        
                        show_pdf(os.path.join(dir, annotated_doc))                  
                with download:
                    with open(os.path.join(dir, annotated_doc), "rb") as pdf_file:
                        PDFbyte = pdf_file.read()
                    st.download_button(label="Download PDF", key=next(widget_id),
                            data=PDFbyte,
                            file_name=f'annotated_{anno_doc_name}',
                            mime='application/octet-stream')
                st.divider()
else:
    st.markdown('*No annotated documents from this session.*')