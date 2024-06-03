from langchain_cohere.llms import Cohere
from langchain_cohere import CohereRerank
from langchain.retrievers import ContextualCompressionRetriever
from openai import OpenAI
import os
import chromadb
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import chromadb.utils.embedding_functions as embedding_functions


class StateOfIncorporation:
    """Rag Application Class
    """
    def __init__(self):
        """Init all class variables, sets the prompt, connects to our chroma db, creates a retriever, searches the chroma db and finds all unique files in our vectorstore, stores the collection.
        """
        self.prompt = """You are an intelligent assistant designed to extract the state of incorporation about a company given documents related to it.
                        The state of incorporation is always on the first page of the doucment. Ouput the state as A SINGLE WORD. NOTHING ELSE."""
        self.client = chromadb.PersistentClient(path='db')
        self.vectorstore = Chroma(
            client=self.client,
            collection_name="docs_collection",
            embedding_function=OpenAIEmbeddings()
        )
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k":50})
        # self.vectorstore_files = set()
        # for pair in self.vectorstore.get()['metadatas']:
        #     self.vectorstore_files.add(pair['file path'])
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=os.environ['OPENAI_API_KEY']
            )
        self.collection = self.client.get_collection(name='docs_collection', embedding_function=openai_ef)

    def compressed_vector_search(self, question):
        """Vector search with rerank functionality

        Args:
            question (str): question we want to pass to vector store to get context documents

        Returns:
            list: list of 5 documents most relevant to our search
        """
        llm = Cohere(temperature=0) # Do we need this ilne
        compressor = CohereRerank(top_n=5)
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=compressor,
            base_retriever=self.retriever,
        )
        compressed_docs = compression_retriever.invoke(question)
        return compressed_docs
    
    def ask_question(self, question):
        """Asks the llm a question, finds the top 5 most related documents in the vector store and queries the llm.

        Args:
            question (str): question we want to ask

        Returns:
            str: llm response
        """
        question = question.lower()
        docs = self.compressed_vector_search(question)

        client = OpenAI()

        completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": self.prompt},
            {"role": "system", "content": f"confine your search within the following knowledge base: {docs}"},
            {"role": "user", "content": question}
        ]
        )
        return completion.choices[0].message.content 
    
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

