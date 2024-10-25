from abc import ABC, abstractmethod
import json
import pandas as pd
from llama_index.core import Document, GPTVectorStoreIndex, PromptHelper, ServiceContext
from langchain import OpenAI
from langchain.prompts import PromptTemplate
import os

# Set your OpenAI API key
os.environ["OPENAI_API_KEY"] = "sk-proj-HwFPBND26SnyzXe8nuXgT3BlbkFJ4CQ71wBNBpziW0et7UGh"

# Abstract summarizer class
class AbstractSummarizer(ABC):
    @abstractmethod
    def __init__(self, knowledge_base_path):
        pass

    @abstractmethod
    def summarize(self, transcript_path):
        pass

# AssessmentPlanExtractor class
class AssessmentPlanExtractor(AbstractSummarizer):
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
        # Retrieve documents from the index using the query
        retriever = self.index.as_retriever(verbose=True)
        search_results = retriever.retrieve(query)

        # Combine the texts of the top results, limiting the total length
        combined_text = ""
        for result in search_results:
            combined_text += result.text.replace("Patient", "Other Patient") + "\n"
            if len(combined_text.split()) > 3000:  # Adjust this limit as needed
                break

        return combined_text

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
                "Based on the provided clinical conversation between the doctor and the patient, generate a detailed Assessment Plan. "
                "The Assessment Plan should include only the doctor's assessment and plan, clearly separated into two sections: Assessment and Plan. "
                "Each section should be detailed and follow the structure provided in the conversation.\n\n"
                "Conversation Transcript:\n{transcript}\n\n"
                "Assessment:\n"
                "Provide a detailed assessment of the patient's condition based on the Conversation Transcript.\n\n"
                "Plan:\n"
                "1. List only the results of diagnostic tests given to the patient mentioned in Transcript Conversation.\n"
                "2. Include any relevant diagnostic results, such as EKG findings, if mentioned in the Transcript Conversation.\n"
                "3. Mention the diagnosis and follow-up instructions provided by the doctor in Transcript Conversation.\n"
                "Ensure not to include any medications or treatments that are not mentioned explicitly in the transcript.\n\n"
                "Please ensure the assessment plan is comprehensive, clear, and formatted properly."
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
    summarizer = AssessmentPlanExtractor(knowledge_base_path)
    return summarizer.summarize(transcript_path)

# Example usage
transcript_path = '/content/June12-01_AbdominalPain.json'
knowledge_base_path = '/content/MTS-Dialog-TestSet-1-MEDIQA-Chat-2023.csv'
summary = execute(transcript_path, knowledge_base_path)
print(summary)


                
                