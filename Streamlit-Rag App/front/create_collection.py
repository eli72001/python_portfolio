import os
import re
import json
import chromadb
from langchain_text_splitters import SpacyTextSplitter
from langchain.document_loaders import PyPDFLoader
from langchain.docstore.document import Document
import chromadb.utils.embedding_functions as embedding_functions

# Preprocessing: Loading, Cleaning, Chunking and Combine Chunks

def clean_text(txt):
    return txt.replace('\n', ' ').replace('\t', ' ') # Removes new line and tab characters

def load_pdf(filename):
    loader = PyPDFLoader(filename)
    pattern = r'^[\d/]+$'
    clean_data = []
    data = loader.load() # Returns a list of documents for every page of the pdf not cleaned
    cik = get_cik(data[0])
    cleaned = clean_pages(data)
    for page in cleaned:
        page.page_content = clean_text(page.page_content)
        if bool(re.match(pattern, page.page_content)) == False:
            clean_data.append(page)
    return cik, clean_data 

def clean_pages(pages): # Removes start of 
    for page in pages:
        benchmark = -1
        page_arr = page.page_content.split(' ')
        for index, text in enumerate(page_arr):
            if index > 10:
                break
            if 'https' in text:
                benchmark = index
                break
        if benchmark > 0:
            clean_content = page_arr[benchmark+1:]
            page.page_content = ' '.join(clean_content)    

    return pages

def combine_chunks(docs, company, file_path, file_type, cik, n):
    combine_docs = []
    for i in range(len(docs)-n):
        page_content = ""
        pages_arr = []
        for j in range(n+1):
            page_content += docs[i+j].page_content
            pages_arr.append(f"{docs[i+j].metadata['page']}")
        pages_arr = [pages_arr[0], pages_arr[-1]]
        if len(pages_arr) > 1:
            pages = '-'.join(pages_arr)
        else:
            pages = pages_arr[0]
        new_doc = Document(page_content=page_content, metadata={"file path": file_path, "company": company, "file_type": file_type, "cik": cik, "page": pages})
        combine_docs.append(new_doc)
    return combine_docs

def chunk_combined_docs(combined_chunks, size):
    final_chunks = []
    text_splitter = SpacyTextSplitter(chunk_size=size)
    for doc in combined_chunks:
        chunks = text_splitter.split_text(doc.page_content)
        for txt in chunks:
            new_doc = Document(page_content=txt, metadata=doc.metadata)
            final_chunks.append(new_doc)
    return final_chunks

def pretty_print(output_string):
    for item in output_string.split('\n'):
        print(item)

# Get the list of all files and directories
def get_doc_names(path):
    file_list = os.listdir(path)
    return file_list

# Get metadatas from file name
def get_metadatas(file_name):
    company = file_name.split()[0]
    file_type = file_name.split()[1].split(".")[0]
    return company, file_type

# Add document chunks to collection
def add_doc_to_collection(collection, final_chunks):
    # Gather documents, metadatas and ids to add to collection
    documents = []
    metadatas = []
    ids = []

    cur_count = collection.count()

    for i in range(len(final_chunks)):
        ids.append('id' + str(cur_count + i + 1))
        documents.append(final_chunks[i].page_content)
        metadatas.append(final_chunks[i].metadata)

    # Add to collection
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

def get_cik(page):
    try:
        for words in page.page_content.split(' '):
            if 'https' in words:
                splits = words.split('/')
                nums = []
                pattern = r'^\d+$'
                for s in splits:
                    if re.match(pattern, s):
                        nums.append(s)
                if nums:
                    return nums[0]
                else:
                    print("CIK could not be extracted")
                    return -1
    except Exception as err:
        print("CIK Could not be extracted from this document")
        return -1
    print("CIK could not be extracted from this doc")
    return -1

# Add json chunk to collection
def add_json_to_collection(collection, json, file_path):
    json_chunk = [str(json)]
    cur_count = collection.count()
    ids = ['id' + str(cur_count + 1)]

    # Add to collection
    collection.add(
        documents=json_chunk,
        metadatas=[{"file path": file_path, "source": "OpenCorporates", "file_type": "json"}],
        ids=ids
    )

def create_collection(name):
    db_path = "db"

# Define collection name
    collection_name = name

    # Define embedding function
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                    api_key=os.environ['OPENAI_API_KEY']
                )
    # Establish connection to chroma server
    client = chromadb.PersistentClient(path=db_path)

    # Uncomment to delete collection
    #client.delete_collection(name="docs_collection")

    # Create a new collection
    collection = client.create_collection(name=collection_name, embedding_function=openai_ef)
    file_list = get_doc_names("company-10ks")

    for file in file_list:
        # Get metadatas
        company, file_type = get_metadatas(file)

        # Load file
        path = "company-10ks/" + file
        cik, pdf_chunks = load_pdf(path)

        # Preprocess file: cleaning, chunking, combining chunks
        #clean_chunks = clean_pages(pdf_chunks)
        combined_chunks = combine_chunks(pdf_chunks, company, file, file_type, cik, 1)
        final_chunks = chunk_combined_docs(combined_chunks, 2000)

        # Add final chunks with metadatas to chromadb collection
        add_doc_to_collection(collection, final_chunks)

    json_list = get_doc_names("company_json")

    for json_file in json_list:
        path = "company_json/" + json_file
        f = open(path)
        data = json.load(f)
        add_json_to_collection(collection, data, json_file)
    
    return collection

def delete_collection(name):
    db_path = "db"
    # Establish connection to chroma server
    client = chromadb.PersistentClient(path=db_path)

    # Uncomment to delete collection
    client.delete_collection(name=name)