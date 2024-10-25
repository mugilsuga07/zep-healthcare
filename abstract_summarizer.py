from .base_summarizer import BaseSummarizer
from langchain.prompts import PromptTemplate
from customstore import CustomStore

class AbstractSummarizer(BaseSummarizer):
    def __init__(self, knowledge_base_path):
        super().__init__(knowledge_base_path)
        self.store = CustomStore(db_name='your_db_name', user='your_user', password='your_password')

    def summarize(self, transcript_path):
        prompt_template = PromptTemplate(
            input_variables=["transcript", "knowledge_base"],
            template=(
                "The following is a clinical conversation between a doctor and a patient. "
                "Based on this conversation transcript and using relevant information from the provided knowledgebase, "
                "generate an abstract summarizing the key points discussed. "
                "Please ensure the abstract is concise and highlights the main concerns, findings, and recommendations."
            )
        )
        
        
        summary = self.generate_summary(transcript_path, prompt_template)
        
        
        self.store.save_data('summary', summary)
        
        return summary

    def __del__(self):
        self.store.close()

