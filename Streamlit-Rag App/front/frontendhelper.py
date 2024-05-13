import base64
import streamlit as st
import os
from OutputParser import OutputParser
from PdfAnnotator import PdfAnnotator
from create_collection import create_collection

def clean_path(path):
    first_split = path.split('\\')
    name = "\\".join(first_split[-2:])
    split = name.split('.')
    split[-1] = '.pdf' 
    return "".join(split)

def show_pdf(file_path):
    with open(file_path,"rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


def get_filename(file_path):
    base = os.path.basename(file_path)
    base_arr = base.split('.')
    return base_arr[0]


def annotate_pdf():
    session_id = st.session_state.sessionId
    response = st.session_state.response
    parser = st.session_state.parser
    try:
        if 'pdf' in parser.get_file():
            if parser.get_file() in st.session_state.annotators.keys():
                annotator = st.session_state.annotators[parser.get_file()]
            else:
                annotator = PdfAnnotator(parser.get_file())
                st.session_state.annotators[parser.get_file()] = annotator
            annotator.highlight(parser, response)
            path = os.path.join('annotated_docs', session_id)
            if os.path.isdir(path) is False:
                os.makedirs(path)
            annotator.save_new_pdf(os.path.join(path, os.path.basename(parser.get_file())))
            return annotator
        else:
            print("PDF FAILING")
            raise Exception
    except Exception as err:
        st.write("Sorry, there was an error trying to annotate the pdf. Please ask your question again!")
        return None
    
def check_collection():
    if os.path.isdir('db') is False:
        create_collection('docs_collection')


def get_session_id():
    from streamlit.runtime import get_instance
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    runtime = get_instance()
    session_id = get_script_run_ctx().session_id
    session_info = runtime._session_mgr.get_session_info(session_id)
    if session_info is None:
        raise RuntimeError("Couldn't get your Streamlit Session object.")
    return session_info.session.id

def check_env_variables():
    try:
        if os.environ.get('OPENAI_API_KEY') is None:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
    except KeyError:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    try:
        if os.environ.get('COHERE_API_KEY') is None:
            raise ValueError("COHERE_API_KEY environment variable is not set")
    except KeyError:
        raise ValueError("COHERE_API_KEY environment variable is not set")
