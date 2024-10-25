from abc import ABC, abstractmethod
import json
import pandas as pd
from llama_index.core import Document, GPTVectorStoreIndex, PromptHelper, ServiceContext
from langchain import OpenAI
from langchain.prompts import PromptTemplate
import os

# OpenAI API key
os.environ["OPENAI_API_KEY"] = "sk-proj-HwFPBND26SnyzXe8nuXgT3BlbkFJ4CQ71wBNBpziW0et7UGh"

# Abstract summarizer class
class AbstractSummarizer(ABC):
    @abstractmethod
    def __init__(self, knowledge_base_path):
        pass

    @abstractmethod
    def summarize(self, transcript_path):
        pass

# Hpisummary class
class Hiisummary(AbstractSummarizer):
    def __init__(self, knowledge_base_path):
        self.knowledge_base_path = knowledge_base_path
        self.knowledge_base = self.load_knowledge_base()
        self.index = self.create_index()

    def load_knowledge_base(self):
        # Loading the CSV file as a string
        df = pd.read_csv(self.knowledge_base_path)
        return df.to_string()

    def create_index(self):
        # Creating a document list
        documents = [Document(text=self.knowledge_base)]

        # Initializing required components for ServiceContext
        prompt_helper = PromptHelper(chunk_size_limit=4096, num_output=512, chunk_overlap_ratio=0.2)
        service_context = ServiceContext.from_defaults(prompt_helper=prompt_helper)

        # Creating and returning the index
        return GPTVectorStoreIndex.from_documents(documents, service_context=service_context)

    def search_index(self, query):
        # Searching for relevant documents in the index
        results = self.retrieve_relevant_documents(query)
        return results

    def retrieve_relevant_documents(self, query):
        # Retrieving documents from the index
        retriever = self.index.as_retriever(verbose=True)
        search_results = retriever.retrieve(query)

        # Combining the texts of the top 5 results
        return "\n".join([result.text.replace("Patient", "Other Patient") for result in search_results[:5]])

    def summarize(self, transcript_path):
        # Loading the transcript JSON file
        with open(transcript_path, 'r') as file:
            transcript_data = json.load(file)

        # Extracting the conversation text
        docs = [item['alternatives'][0]['content'] for item in transcript_data['results']['items'] if 'alternatives' in item and item['alternatives']]
        transcript_text = " ".join(docs)

        # Retrieving relevant knowledge base entries
        relevant_knowledge_base = self.search_index(transcript_text)

        prompt_template = PromptTemplate(
            input_variables=["transcript", "knowledge_base"],
            template=(
                "The following is a clinical conversation between a doctor and a patient. "
                "Based on this conversation transcript and using relevant information from the provided knowledgebase, "
                "generate a detailed History of Present Illness (HPI) for the patient. The HPI should include the following sections:\n\n"
                "1. Chief Complaint: Brief description of only the primary symptom. Don't mention the age of the patient.\n"
                "2. Previous Occurrences: Any similar past episodes.\n"
                "3. Family History: Relevant family medical history.\n"
                "4. Symptoms: only current symptoms.\n\n"
                "Conversation Transcript:\n{transcript}\n\n"
                "Relevant Knowledge Base:\n{knowledge_base}\n\n"
                "Please ensure the HPI is comprehensive, clear, and formatted properly."
            )
        )

        # Generating the summary using the LLM
        llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        prompt = prompt_template.format(transcript=transcript_text, knowledge_base=relevant_knowledge_base)
        summary = llm(prompt)
        return summary

# Execute function
def execute(transcript_path, knowledge_base_path):
    # Generating the summary
    summarizer = Hiisummary(knowledge_base_path)
    return summarizer.summarize(transcript_path)

transcript_path = '/content/June12-01_AbdominalPain.json'
knowledge_base_path = '/content/MTS-Dialog-TestSet-1-MEDIQA-Chat-2023.csv'
summary = execute(transcript_path, knowledge_base_path)
print(summary)




