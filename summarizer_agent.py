from llama_index.core import SimpleDirectoryReader
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
)
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter

class SummarizerAgent:
    def __init__(
        self,
        llm_model_name,
        summary_prompt,
        post_prompt,
        vector_store,
        kb_metadata=None,
        document_location=None,
    ):
        self.llm_model_name = llm_model_name
        self.summary_prompt = summary_prompt
        self.post_prompt = post_prompt
        self.document_location = document_location
        self.kb_metadata = kb_metadata
        self.vector_store = vector_store

        self.create_index()

    def create_index(self):
        if self.document_location is None:
            print("no index to process")
            return

        reader = SimpleDirectoryReader(input_dir=self.document_location)
        documents = reader.load_data()
        index_loaded = False
        storage_context = None
        try:
            storage_context = StorageContext.from_defaults(
                vector_store=self.vector_store
            )
            self.data_index = load_index_from_storage(storage_context)
            index_loaded = True
        except:
            index_loaded = False
        if not index_loaded:
            print("create_index")
            self.data_index = VectorStoreIndex.from_documents(
                documents, storage_context=storage_context, kb_metadata=self.kb_metadata
            )

    def retrieve_relevant_documents(self, query):
        if self.document_location is None:
            print("no index to process")
            return []

        retriever = self.data_index.as_retriever(verbose=True)
        search_results = retriever.retrieve(query)
        return "\n".join(search_results)

    def summarize(self, text_to_summarize):
        try:
            llm = ChatOpenAI(model=self.llm_model_name)
            text_splitter = RecursiveCharacterTextSplitter(
                separators=["\n\n", "\n"], chunk_size=3000, chunk_overlap=500
            )

            docs = text_splitter.create_documents([text_to_summarize])
            num_docs = len(docs)
            print(f"Now we have {num_docs} documents")

            # Combined map and reduce prompts
            combined_prompt_template = PromptTemplate(
                template=self.summary_prompt + self.post_prompt, input_variables=["text"]
            )

            summary_chain = load_summarize_chain(
                llm=llm,
                chain_type="map_reduce",
                map_prompt=combined_prompt_template,
                combine_prompt=combined_prompt_template,
                verbose=True
            )
            summary = summary_chain.run(docs)
            return summary
        except Exception as e:
            print(e)
            print("failed to summarize")




