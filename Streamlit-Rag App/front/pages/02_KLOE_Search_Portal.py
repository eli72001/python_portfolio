import streamlit as st
import tempfile
from OutputParser import OutputParser
from RagApplication import RagApplication
import io
import os
from dotenv import load_dotenv
from OpenCorporates import OpenCorporates
from StateOfIncorporation import StateOfIncorporation
import json
from frontendhelper import search_nasdaq, clean_path, show_pdf, annotate_pdf, check_collection, get_session_id, check_env_variables, get_messages
from streamlit_extras.app_logo import add_logo
from EdgarScrape import SecPdfDownloader
import time
from streamlit_searchbox import st_searchbox

if "ticker_cache" not in st.session_state:
    st.session_state.ticker_cache=[]
if "annotators" not in st.session_state:
    st.session_state.annotators = {}
if "parser" not in st.session_state:
    st.session_state.parser = None
if "response" not in st.session_state:
    st.session_state.response = None

if "sessionId" not in st.session_state:
    st.session_state.sessionId = get_session_id()

if "ticker" not in st.session_state:
    st.session_state.ticker = ""
if "widget" not in st.session_state:
    st.session_state.widget = None
if "ticker_success" not in st.session_state:
    st.session_state.ticker_success = False

e_1 = time.time()
if "rag_app" not in st.session_state:
    st.session_state.rag_app = RagApplication()
if "state_app" not in st.session_state:
    st.session_state.state_app = StateOfIncorporation()
if "sec_downloader" not in st.session_state:
    st.session_state.sec_downloader = SecPdfDownloader()
e_2 = time.time()
if e_2-e_1 > 0:
    print(f'VAR INITIALIZATIONS: {e_2-e_1}')

st.set_page_config(page_title='KLOE Search Portal', layout='wide')

############ ARIAL FONT  ##################

st.markdown("""

<style>
body {

    font-family: 'Arial';

}
</style>

""", unsafe_allow_html=True)

############ HEADER #########################

with st.container():
    kb, pipe, db = st.columns((.8,.2,5.3))
    with kb:
        st.image(r'ui_assets\kloe_pos.png', width=90)
    

st.write('') 

html = """
<html>
<head>
    <style>
        p {font-family: Arial;}
        .white-text { color: #FFFFFF; }
        .black-text { color: #000000; }
        .red-text { color: #FF0000; }
        .header { font-size: 40px; font-weight: bolder; }
    </style>
</head>
<body>
    <p class="black-text">Welcome to the KLOE Search Portal. Find the answers you need for your KYC requirements in a click.</p>
</body>
</html>
"""
st.markdown(html, unsafe_allow_html=True)


st.divider()

#### SIDEBAR #####################

add_logo(r'ui_assets\kb_logo_small.png', height=5)

def submit():
    f_1 = time.time()
    st.session_state.ticker = st.session_state.widget
    st.session_state.sec_downloader.download_pdf_and_json(st.session_state.ticker)
    st.session_state.ticker_success = True
    st.session_state.widget = ''
    f_2 = time.time()
    print(f'Total Download Time Ticker (PDF AND JSON): {f_2-f_1}')
with st.sidebar:
    st.markdown('**User Sources**')
    selected_value = st_searchbox(search_nasdaq, key="nasdaq_search")
    if selected_value:
        if selected_value not in st.session_state.ticker_cache:
            st.session_state.sec_downloader.download_pdf_and_json(selected_value)
            st.session_state.ticker_cache.append(selected_value)
            st.write(f"{selected_value} Successfully Added to Collection!")
    
    st.caption('-or-')

    uploaded_files = st.file_uploader("Import a new PDF/document", accept_multiple_files = True, type=['pdf'], help='Upload a PDF file for processing.') 
    for uploaded_file in uploaded_files:
        if uploaded_file is not None:
            g_1 = time.time()
            i1 = time.time()
            file_info = {"name": uploaded_file.name, "size": uploaded_file.size}
            
            with tempfile.NamedTemporaryFile(delete=False, dir='company-10ks', prefix=uploaded_file.name) as tmpfile:
                cleaned_path = clean_path(tmpfile.name)
                if st.session_state.rag_app.check_vectorstore(cleaned_path):
                    with open(cleaned_path, 'wb') as cleaned_file:
                        cleaned_file.write(uploaded_file.getvalue())
                    tmpfile_path = cleaned_path
                    file_to_remove = tmpfile.name
                else:
                    file_to_remove = tmpfile.name
            os.remove(file_to_remove)
            with st.spinner("Setting up the document..."):
                upload_response = st.session_state.rag_app.add_document(tmpfile_path)
                i2 = time.time()
                print(f'ONLY PDF FILE UPLOAD: {i2-i1}')
                st.success(upload_response)
                # Get json only when uploaded doc does not already exist
                if upload_response == "Successfully Added to Collection":
                    h1 = time.time()
                    company_name = tmpfile_path.split("\\")[-1].split(" ")[0]

                    question = f"What is the state of incorporation of {company_name}"

                    state_of_incorporation = st.session_state.state_app.ask_question(question)

                    jurisdiction_code = OpenCorporates.get_jurisdiction_code(state_of_incorporation, 'jurisdiction.json')

                    company_data = OpenCorporates.loose_search_api(company_name, jurisdiction_code, os.environ['OPENCORPORATE_API_KEY'])
                    company_number = OpenCorporates.get_company_number(company_data)
                    full_data = OpenCorporates.call_api(jurisdiction_code, company_number, os.environ['OPENCORPORATE_API_KEY'])
                    clean_data = OpenCorporates.clean_data(OpenCorporates, full_data)

                    # Add json to collection
                    st.session_state.state_app.add_json_to_collection(clean_data, company_name+".json")
                    # Save json to folder
                    with open(f'company_json/{company_name}.json', 'w') as file:
                        json.dump(clean_data, file)
                    h2=time.time()
                    g_2 = time.time()
                    print(f'JSON UPLOAD ONLY (FILE UPLOAD): {h2-h1}')
                    print(f'FILE UPLOAD TOTAL TIME: {g_2-g_1}')

    

### CHATBOT #####

kubrick_avatar = r'ui_assets\kb4.png'
user_avatar = r'ui_assets\user.png' 
st.session_state.messages = get_messages()

for message in st.session_state.messages:
    if message['role'] == 'user':
        st.chat_message(message['role'], avatar=user_avatar).write(message['content'])
    else:
        st.chat_message(message['role'], avatar=kubrick_avatar).write(message['content'])


if question := st.chat_input():
    j1 = time.time()
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user", avatar = user_avatar):
        st.markdown(question)
    with st.chat_message("assistant", avatar = kubrick_avatar):
        with st.spinner('Thinking...'):
            response = st.session_state.rag_app.ask_question(question)
            st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response}) #### Version 2 --- change 'response' to 'f'ull_response' and unmark lines for version 1
            try:
                refined_response = st.session_state.rag_app.refine_output(response, question)
                print(refined_response)
                parser = OutputParser(refined_response)
                st.session_state.parser = parser
                st.session_state.question = question
                st.session_state.response = refined_response
                j2 = time.time()
                print(f'TOTAL ANSWER TIME: {j2-j1}')
                if 'pdf' not in parser.get_file():
                    st.warning("*Please note: Annotations are unavailable for non-PDF files.")
            except Exception as err:
                st.warning("Sorry, there was an error trying to annotate the pdf. Please ask your question again!")

try:
    if (st.session_state.parser) and ('pdf' in st.session_state.parser.get_file()): # AND SHOW_ANNOTATOR_BUTTON???
        anno_btn, preview_btn, download_btn, success = st.columns((1,1,1,3))
        with anno_btn:
            if st.button("Annotate PDF"):
                annotator = annotate_pdf()
                try:
                    if annotator.file_path:
                        anno_doc = annotator.file_path
                        file_size = os.path.getsize(anno_doc)
                        if file_size < 2000000:
                            with preview_btn:
                                with st.popover('Preview PDF'):
                                    show_pdf(annotator.file_path)
                            with download_btn:
                                with open(anno_doc, "rb") as pdf_file:
                                    PDFbyte = pdf_file.read()
                                    st.download_button(label="Download PDF", key='123',
                                        data=PDFbyte,
                                        file_name=f'annotated_{os.path.basename(anno_doc)}',
                                        mime='application/octet-stream')
                            with success:
                                st.caption('Document annotated successfully!')
                        else:
                            with preview_btn:
                                # now is download button
                                with open(anno_doc, "rb") as pdf_file:
                                    PDFbyte = pdf_file.read()
                                    st.download_button(label="Download PDF", key='123',
                                        data=PDFbyte,
                                        file_name=f'annotated_{os.path.basename(anno_doc)}',
                                        mime='application/octet-stream')
                            with download_btn:
                                # now is success caption
                                st.caption('Document annotated successfully!')
                            with success:
                                # now is file size warning
                                st.warning('''Please note: this file is over 2MB and cannot be previewed. 
                                        However, you can still download the annotated file here and on the Annotation Hub page.''')
                except Exception as err:
                    st.warning("There was an error annotating. Please try asking your question again.")
except Exception as err:
    pass

