import streamlit as st
import tempfile
from PdfAnnotator import PdfAnnotator
from OutputParser import OutputParser
from RagApplication import RagApplication
import io
import os
from dotenv import load_dotenv
from OpenCorporates import OpenCorporates
from StateOfIncorporation import StateOfIncorporation
from openai import OpenAI
import json
from frontendhelper import clean_path, show_pdf, get_filename, annotate_pdf, check_collection, get_session_id, check_env_variables

load_dotenv()
check_env_variables()


check_collection() ## This is going to take a couple min to load if the database does not exist yet

rag_app = RagApplication()
state_app = StateOfIncorporation()



if "annotators" not in st.session_state:
    st.session_state.annotators = {}
if "parser" not in st.session_state:
    st.session_state.parser = None
if "response" not in st.session_state:
    st.session_state.response = None

if "sessionId" not in st.session_state:
    st.session_state.sessionId = get_session_id()




st.set_page_config(page_title='KYC DocSearch', layout='wide')

#### HEADER #####################

st.image(r'ui_assets\Kubrick_Logo_DarkGreen.png', width=120)
st.title('KYC DocSearch')
st.markdown('Welcome to KYC DocSearch! This system allows you to upload a PDF document and ask questions based on its content.')
with st.container():
    st.success('''
        **TIP**\t|  Try asking questions like: \n
        *"Who signed the documents for company A?"*\n
        *"What is the nature of business for company B?"*\n
        *"What is the business address for company C?"*''')
st.divider()

#### SIDEBAR #####################

with st.sidebar:
    uploaded_files = st.file_uploader("Upload your document", accept_multiple_files = True, type=['pdf'], help='Upload a PDF file for processing.') 
    for uploaded_file in uploaded_files:
        if uploaded_file is not None:
            file_info = {"name": uploaded_file.name, "size": uploaded_file.size}
            
            with tempfile.NamedTemporaryFile(delete=False, dir='company-10ks', prefix=uploaded_file.name) as tmpfile:
                cleaned_path = clean_path(tmpfile.name)
                if rag_app.check_vectorstore(cleaned_path):
                    with open(cleaned_path, 'wb') as cleaned_file:
                        cleaned_file.write(uploaded_file.getvalue())
                    tmpfile_path = cleaned_path
                    file_to_remove = tmpfile.name
                else:
                    file_to_remove = tmpfile.name
            os.remove(file_to_remove)
            with st.spinner("Setting up the document..."):
                upload_response = rag_app.add_document(tmpfile_path)
                st.write(upload_response)
                # Get json only when uploaded doc does not already exist
                if upload_response == "Successfully Added to Collection":
                    token = 'tzrBWpC8Xz1B3nGMqDAJ'

                    company_name = tmpfile_path.split("\\")[-1].split(" ")[0]
                    print("EXTRACTED COMPANY NAME: ", company_name)
                    print(company_name)

                    question = f"What is the state of incorporation of {company_name}"

                    state_of_incorporation = state_app.ask_question(question)
                    print("---------------------------------")
                    print("State of Incorporation: ", state_of_incorporation)

                    jurisdiction_code = OpenCorporates.get_jurisdiction_code(state_of_incorporation, 'jurisdiction.json')
                    print("---------------------------------")
                    print("Jurisdiction Code: ", jurisdiction_code)

                    company_data = OpenCorporates.loose_search_api(company_name, jurisdiction_code, token)
                    clean_data = OpenCorporates.clean_data(OpenCorporates, company_data)
                    print("---------------------------------")
                    print(clean_data)
                    print(type(clean_data))

                    # Add json to collection
                    state_app.add_json_to_collection(clean_data, company_name+".json")
                    # Save json to folder
                    with open(f'company_json/{company_name}.json', 'w') as file:
                        json.dump(clean_data, file)


    

### CHATBOT #####

kubrick_avatar = r'ui_assets\kubrick_icon2.png'
user_avatar = r'ui_assets\user_icon.png'

if "messages" not in st.session_state:
    st.session_state['messages'] = []
    # st.markdown('*Upload a file into sidebar and type a question into the text box below to get started.*')
    with st.chat_message("assistant", avatar = kubrick_avatar):
        st.markdown('Upload a file into sidebar and type a question into the text box below to get started.')

for message in st.session_state.messages:
    if message['role'] == 'user':
        st.chat_message(message['role'], avatar=user_avatar).write(message['content'])
    else:
        st.chat_message(message['role'], avatar=kubrick_avatar).write(message['content'])


if question := st.chat_input():
    # st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user", avatar = user_avatar):
        st.markdown(question)
    with st.chat_message("assistant", avatar = kubrick_avatar):
        with st.spinner('Thinking...'):
            response = rag_app.ask_question(question)
            st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response}) #### Version 2 --- change 'response' to 'f'ull_response' and unmark lines for version 1
            try:
                refined_response = rag_app.refine_output(response, question)
                parser = OutputParser(refined_response)
                st.session_state.parser = parser
                st.session_state.response = refined_response
                if 'pdf' not in parser.get_file():
                    st.warning("A PDF Document was not found to annotate")
            except Exception as err:
                st.warning("Sorry, there was an error trying to annotate the pdf. Please ask your question again!")


if (st.session_state.parser) and ('pdf' in st.session_state.parser.get_file()): # AND SHOW_ANNOTATOR_BUTTON???
    anno_btn, preview_btn, download_btn, success = st.columns((1,1,1,3))
    with anno_btn:
        if st.button("Annotate PDF"):
            annotator = annotate_pdf()
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
                                   However, you can still download the annotated file here and on the Annotation Download page.''')


    
