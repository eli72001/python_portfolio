from langchain.document_loaders import PyPDFLoader
from langchain_text_splitters import SpacyTextSplitter
from langchain.docstore.document import Document
import os

import re

class CustomDocument:
    """Custom document class to load chunk and create the metadata before embedding
    """

    def __init__(self, file_name):
        """Initializer Class that sets class variables

        Args:
            file_name (str): path of pdf we want to load
        """
        self.file_name = file_name
        self.clean_data = None
        self.combined_data = None
        self.combined_chunks = None
        self.cik = None
    
    # Helper Functions

    @staticmethod
    def clean_text(txt):
        """Static Method that removes new lines and tab characters from a string

        Args:
            txt (str): string to clean

        Returns:
            str: cleaned string
        """
        cleaned = txt.replace('\n', ' ').replace('\t', ' ')
        return cleaned
    
    def filter_cik(self, cik):
        """Helper function that takes a chunk of text from a uncleaned page and filters out the CIK number

        Args:
            cik (str): string with cik number inside

        Returns:
            str: -1 if the cik number is not found. Sets the document.cik class variables if the cik number is found
        """
        try:
            splits = cik.split('/')
            nums = []
            pattern = r'^\d+$'
            for s in splits:
                if re.match(pattern, s):
                    nums.append(s)
            if nums:
                self.cik = nums[0]
            else:
                print("CIK could not be extracted")

        except Exception as err:
            print("CIK Could not be extracted from this document")
            return -1
    
    def clean_pages(self, data):
        """Helper function to clean every page of a pdf, removing the header, getting the cik number.

        Args:
            data (List): List of Langchain Documents consisted of singular pages from the PDF we uploaded

        Returns:
            list: list of clean langchain documents 
        """
        i = 0 
        for page in data:
            benchmark = -1
            page_arr = page.page_content.split(' ')
            for index, text in enumerate(page_arr):
                if index > 10: # Only check for header in first couple words
                    break
                if 'https' in text:
                    benchmark = index
                    if self.cik == None and i == 0:
                        self.filter_cik(text)
                    break
            if benchmark > 0:
                clean_content = page_arr[benchmark+1:]
                page.page_content = ' '.join(clean_content)    
            i+=1
        return data
    
    def load_pdf(self):
        """Loads a pdf, cleaning every page by removing the header and new line characters/tab characters. Also gets rid of empty pages and sets the cik number if it exists

        Returns:
            list: List of llanchain documents for every clean page
        """
        loader = PyPDFLoader(self.file_name)
        pattern = r'^[\d/]+$'
        clean_data = []
        data = loader.load() # Returns a list of documents for every page of the pdf not cleaned
        clean_pages = self.clean_pages(data)
        for page in clean_pages:
            page.page_content = CustomDocument.clean_text(page.page_content)
            if bool(re.match(pattern, page.page_content)) == False:
                clean_data.append(page)
        self.clean_data = clean_data
        return self.clean_data
    
    def combine_chunks(self, n=1):
        """Combines pages of our document to add context

        Args:
            n (int, optional): Number of pages to overlap. Defaults to 1.

        Returns:
            list: List of Langchain documents with 1 page overlap
        """
        combine_docs = []
        for i in range(len(self.clean_data)-n):
            page_content = ""
            pages_arr = []
            for j in range(n+1):
                page_content += self.clean_data[i+j].page_content
                pages_arr.append(f"{(self.clean_data[i+j].metadata['page'])}")
            pages_arr = [pages_arr[0], pages_arr[-1]]
            if len(pages_arr)>1:
                pages = '-'.join(pages_arr)
            else:
                pages = pages_arr[0]
            new_doc = Document(page_content=page_content, metadata={"file path":os.path.basename(self.clean_data[0].metadata['source']), "page": pages})
            combine_docs.append(new_doc)
        self.combined_data = combine_docs
        return self.combined_data
    
    def chunk_combined_docs(self, size):
        """Chunks documents into a specific character size

        Args:
            size (int): number of characters in a chunk

        Returns:
            list: list of Langchain documents that have been chunked
        """
        final_chunks = []
        text_splitter = SpacyTextSplitter(chunk_size=size)
        for doc in self.combined_data:
            chunks = text_splitter.split_text(doc.page_content)
            for txt in chunks:
                new_doc = Document(page_content=CustomDocument.clean_text(txt), metadata=doc.metadata)
                final_chunks.append(new_doc)
        self.combined_chunks = final_chunks
        return self.combined_chunks
    
    def process_document(self):
        """Driver code that loads the pdf, does the appropriate cleaning, finds the cik, combines the pages to create overlap, and then chunk those into a size of 2000 characters

        Returns:
            list: List of langchain documents that have been appropriately cleaned, combined, and chunked
        """
        # IF PDF:
        self.load_pdf()
        self.combine_chunks()
        self.chunk_combined_docs(2000)
        return self.combined_data
        # IF JSON:

    