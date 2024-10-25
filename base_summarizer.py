import os
import pandas as pd
from pgvector_store import PGVectorStore
from custom_document import Document
from langchain.llms import OpenAI
from llama_index.core import SimpleDirectoryReader

os.environ["OPENAI_API_KEY"] = "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"

class BaseSummarizer:
    def __init__(self, store):
        self.store = store
        self.llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        documents = self.load_kb('C:/Users/ADMIN/OneDrive/Desktop/Healthcare/summarizer/MTS-Dialog-TestSet-1-MEDIQA-Chat-2023.csv')
        self.store.add(documents, kb_metadata={
            'name': 'Healthcare Knowledge Base',
            'data_type': 'text',
            'metadata': {'category': 'medical'},
            'status': 'active'
        })

    def load_kb(self, filepath):
        reader = SimpleDirectoryReader(input_dir=filepath)
        documents = reader.load_data()
        return documents

    def summarize(self, conversation):
        summary = f"Summary of: {conversation}"
        return summary

    def __del__(self):
        import asyncio
        asyncio.run(self.store.async_close())
