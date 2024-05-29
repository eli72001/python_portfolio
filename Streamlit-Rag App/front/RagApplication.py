from langchain_cohere.llms import Cohere
from langchain_cohere import CohereRerank
from langchain.retrievers import ContextualCompressionRetriever
from openai import OpenAI
import chromadb
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import os
from CustomDocument import CustomDocument
import chromadb.utils.embedding_functions as embedding_functions

class RagApplication:
    def __init__(self):
        self.prompt = """You are an intelligent assistant designed to extract information
                        and answer questions about a company given the documents related to it.
                        Use the following pieces of retrieved context to answer the question.
                        Just answer the question, do not provide any introduction text.
                        Also provide the metadata of the document where you find the answer.
                        The File Path of the document should include .pdf if it exists in the metadata.

                        IMPORTANT NOTE: If the question contains a company name NOT exactly as an extracted file name "[company name] 10k" from the metadata, the output should incur an ERROR.
                        Example error:
                            [company name] documents not found.
 
                        Each question should contain a company name found within the file name and metadata. Return error if question contains a company name NOT EXACTLY the same as file name from the metadata.
 
                        1. If the question asks for the nature of the business of a company, the output should be a SINGLE summary sentence.
                        The summary should provide an informative sentence of the company. This can include products and/or services. MAKE IT SPECIFIC AND INFORMATIVE!
                        Do NOT use bulletpoints for this question.
                        Please be succinct and LIMIT to 12 words.
 
                        Example output:
                            [company name] is [a single sentence summarising the nature of business]
 
                            Document: [document here].pdf | Page Number: [page number here]
 
                        Note: Use this for AMAZON:
                           
                            Amazon is a global e-commerce and technology company.
 
                            Document: [document here].pdf | Page Number: [page numbers here]
 
                        Make each simple summary up to ONE SENTENCE and 12 WORDS. Make the simple summary informative and SPECIFIC like the provided example.
                       
                        2. If the question asks for an address or registered address, ONLY look for it in the OpenCorporates json.
                        Use the registered address from OpenCorporates json.
                        This file type is found in the metadata.
                        IMPORTANT: only use the OpenCorporates json file for addresses!
 
                        Next, in the OpenCorporates json file, if "has_registered_address" = false, report the address as agent address.
                        If "has_registered_address" = true, do not report.
                        Do NOT use bulletpoints for this question.
 
                        Extract the "opencorporates_url" from the json file and include it as the document source. Do NOT extract the registry_url!!
 
                        Example output:
                           
                            [address]\n
 
                            This is the company's [agent] address.\n
 
                            Document: OpenCorporates [insert registry_url here] | Page Number: [page number here]
                        
                        Take each address from OpenCorporates company json files. Include the opencorporates_url from the json files and Page Number. Ensure the "has_registered_address" = false reports the address as agent address.
                       
                        3. If the question asks for representatives, look for them in the signature page (usually last few pages) of the document.
                        IMPORTANT: Legal representatives include all listed DIRECTOR and officer even if they did not sign.
                        The output should be a bullet list of identified names and their position separated by a double tick mark '--'.
                       
                        Example output:
                            Here are the legal representatives for [company name]: \n
                            * Elon Musk -- Chief Executive Officer
                            * James Murdoch -- Director
                            ...
 
                            Document: [document here].pdf | Page Number: [page number here]
                       
                        4. If the question is asking for ID number, the output should be in the format:
                            [company name]'s [ID name]:
                            [ID number]
                            ...
 
                            Document: [document here].pdf | Page Number: [page number here]
 
 
                        """
        self.client = chromadb.PersistentClient(path='db')
        self.vectorstore = Chroma(
            client=self.client,
            collection_name="docs_collection",
            embedding_function=OpenAIEmbeddings()
        )
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k":100})
        self.vectorstore_files = set()
        for pair in self.vectorstore.get()['metadatas']:
            self.vectorstore_files.add(pair['file path'])
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=os.environ['OPENAI_API_KEY']
            )
        self.collection = self.client.get_collection(name='docs_collection', embedding_function=openai_ef)
        #self.enc = tiktoken.get_encoding('cl100k_base')

    def compressed_vector_search(self, question):
        llm = Cohere(temperature=0) # Do we need this ilne
        compressor = CohereRerank(top_n=6)
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=compressor,
            base_retriever=self.retriever,
        )
        compressed_docs = compression_retriever.invoke(question)
        return compressed_docs
    
    def ask_question(self, question):
        question = question.lower()
        docs = self.compressed_vector_search(question)
        client = OpenAI()
 
        completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": self.prompt},
            {"role": "system", "content": f"confine your search within the following knowledge base and only use file names found in the metadata of {docs}"},
            {"role": "user", "content": question},
            {"role": "system", "content": "**IMPORTANT**: If asked for legal representatives, INCLUDE ALL LISTED DIRECTOR on signature page. RETURN ALL NAMES!!"}
        ]
        )
        return completion.choices[0].message.content 
    
    """def count_tokens(self, text):
        tokens = self.enc.encode(text)
        return len(tokens)
    
    def refine_documents(self, docs):
        total_tokens = self.count_tokens(self.prompt)
        for doc in docs:
            total_tokens += self.count_tokens(doc.page_content)
        while(total_tokens >= 16385):
            to_remove = self.count_tokens(docs[-1].page_content)
            total_tokens -= to_remove
            docs = docs[0:-1]
        return docs"""

    
    def refine_output(self, output, question):
        prompt = """You are an intelligent assistant designed to extract information 
                    and answer questions about a company given the documents related to it.
                    You will be given pages from a document as context, and a generated answer for a specific question.
                    Your task is to search within the provided context and return an exact match from the text based on the generated answer.
                    Provide the page number and file name at the end of the output.

                    If the question asks for the nature of the business of a company, the output should be an EXACT MATCH from the context provided.
                    Do NOT use bulletpoints for this question.
                    Only use exact quotes from the text.
                    Example output:
                        [exact match of text from context]

                        Document: [document here].pdf | Page Number: [page number here]
                    
                    
                    If the question asks for address, ONLY look for it in the OpenCorporates json. This file type is found in the metadata.
                    Use the registered address from OpenCorporates json. Do NOT use bulletpoints for this question.

                    Next, in the OpenCorporates json file, if "has_registered_address" = false, report the address as AGENT address.
                    If "has_registered_address" = true, do nothing.
                    

                    Example output:
                        
                        [address]\n

                        This is the company's [agent] address.
                        ...

                        Source: [source in metadata]

                    If the question asks for legal representatives, look for them in the signature pages (usually last few pages) of the document and report all of them.
                    Note that legal representatives include ALL LISTED principal officers, directors, and attornies even if they did not sign the document.
                    The output should be a bullet list of identified names and their position, separate the name from the position with two dash marks '--'.
                    
                    Example output:
                        Here are the legal representatives for [company name]: \n
                        * Elon Musk -- Chief Executive Officer
                        * James Murdoch -- Director
                        ...

                        Document: [document here].pdf | Page Number: [page number here]"""

        question = question.lower()
        docs = self.compressed_vector_search(question)

        client = OpenAI()

        completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "system", "content": f"provide document source and associated page_nums for EACH document found in {output}"},
            {"role": "system", "content": f"Confine your search within the following knowledge base: {docs}"},
            {"role": "user", "content": f"Provide an exact match of text for the following answer: {output}"},
            {"role": "system", "content": "**IMPORTANT**: IF asked for address, TAKE FROM THE OPENCORPORATES JSON and return the registry_url as part of the Document:!!"}
           
        ]
        )
        return completion.choices[0].message.content
    
    def add_to_collection(self, collection, final_chunks):
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
    
    def add_document(self, file_path):
        file_name = os.path.basename(file_path)
        if file_name in self.vectorstore_files:
            return f"{file_name} has already been uploaded to vector database"
        else:
            doc = CustomDocument(file_path)
            final_chunks = doc.process_document()
            self.add_to_collection(self.collection, final_chunks)
            self.vectorstore_files.add(file_name)
            return "Successfully Added to Collection"
    
    def get_cik(self, file_path):
        base_file = os.path.basename(file_path)
        for data in self.vectorstore.get()['metadatas']:
            if data['file path'] == base_file:
                try:
                    return data['cik']
                except Exception as err:
                    continue
        print("Could not locate cik")
        return -1
    
    def check_vectorstore(self, file_name):
        if file_name in self.vectorstore_files:
            return False
        return True
    
    def add_json_to_collection(self, json, file_path):
        json_chunk = [str(json)]
        cur_count = self.collection.count()
        ids = ['id' + str(cur_count + 1)]

        # Add to collection
        self.collection.add(
            documents=json_chunk,
            metadatas=[{"file path": file_path, "source": "OpenCorporates", "file_type": "json"}],
            ids=ids
        )