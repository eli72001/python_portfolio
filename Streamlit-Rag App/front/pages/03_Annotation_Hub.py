import streamlit as st
import os
import time
from pathlib import Path
from streamlit_extras.app_logo import add_logo


from frontendhelper import show_pdf

st.set_page_config(page_title='Annotation Hub', layout='wide')

add_logo(r'ui_assets\kb_logo_small.png', height=5)

############### HEADER ######################

with st.container():
    kb, pipe, db = st.columns((.8,.2,5.3))
    with kb:
        st.image(r'ui_assets\kloe_pos.png', width=90)
        
############ ARIAL FONT  ##################

st.markdown("""

<style>
body {

    font-family: 'Arial';

}
</style>

""", unsafe_allow_html=True)

html = """
<html>
<head>
    <style>
        p {font-family: Arial;}
        .black-text { color: #000000; }
        .header { font-size: 40px; font-weight: bolder; }
    </style>
</head>
<body>
    <p class="header">Annotation Hub</p>
    <p class="black-text">All annotated PDFs from your query sessions are saved and available for download here. </p>
</body>
</html>
"""
st.markdown(html, unsafe_allow_html=True)


st.divider()

annotated_docs = 'annotated_docs'
text_search = st.text_input("Search Annotation Hub", placeholder="Insert company name",value="")
# st.divider()
st.write('')
st.write('')

widget_id = (id for id in range(1, 100_00))
if os.listdir(annotated_docs):
    for dir in Path(annotated_docs).iterdir():
        for annotated_doc in os.listdir(dir):
            anno_doc_name = os.path.basename(annotated_doc)
            anno_doc_time = time.ctime(os.path.getmtime(os.path.join(dir, annotated_doc)))
            if text_search.lower() in anno_doc_name.lower():
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