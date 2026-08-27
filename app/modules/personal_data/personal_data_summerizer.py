from app.domain_types.schemas.summerizer_interface import ISummerizer
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI

class Summerizer(ISummerizer):

    def summerize(self, patient_data):
        template = """Following is patient information.

                    {patient_data}

                    Summarize the patient information and don't loose any information while creating the summary

                    """

        prompt = PromptTemplate(
            input_variables=["patient_data"], template=template
        )
        summary_chain = LLMChain(llm=ChatOpenAI(temperature=0, model_name="gpt-4o-mini"), prompt=prompt)
        summary = summary_chain.run(patient_data=patient_data)
        return summary