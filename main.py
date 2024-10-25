import os
from summarizer.hpi_summarizer import HPISummarizer
from summarizer.ros_summarizer import RosSummarizer
from summarizer.physical_exam_summarizer import PhysicalExamSummarizer
from summarizer.assessment_plan_summarizer import AssessmentPlanSummarizer


os.environ["OPENAI_API_KEY"] = "sk-proj-HwFPBND26SnyzXe8nuXgT3BlbkFJ4CQ71wBNBpziW0et7UGh"

def execute_summarizer(summarizer_strategy, transcript_path, knowledge_base_path):
    if summarizer_strategy == 'Hpi':
        summarizer = HPISummarizer(knowledge_base_path)
    elif summarizer_strategy == 'Ros':
        summarizer = RosSummarizer(knowledge_base_path)
    elif summarizer_strategy == 'PhysicalExam':
        summarizer = PhysicalExamSummarizer(knowledge_base_path)
    else:
        summarizer = AssessmentPlanSummarizer(knowledge_base_path)
        
    summary = summarizer.summarize(transcript_path)
    print(summary)

if __name__ == "__main__":
    transcript_path = 'C:/Users/ADMIN/OneDrive/Desktop/Healthcare/summarizer/June12-01_AbdominalPain copy.json'
    knowledge_base_path = 'C:/Users/ADMIN/OneDrive/Desktop/Healthcare/summarizer/MTS-Dialog-TestSet-1-MEDIQA-Chat-2023.csv'
    
    print("HPI Summary:") 
    execute_summarizer('Hpi', transcript_path, knowledge_base_path)

    print("\nROS Summary:")
    execute_summarizer('Ros', transcript_path, knowledge_base_path)

    print("\nPhysical Exam Summary:")
    execute_summarizer('PhysicalExam', transcript_path, knowledge_base_path)

    print("\nAssessment Plan Summary:")
    execute_summarizer('AssessmentPlan', transcript_path, knowledge_base_path)
