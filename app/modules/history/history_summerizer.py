
from app.domain_types.schemas.summerizer_interface import ISummerizer
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI

class Summerizer(ISummerizer):

    def summerize(self, group_of_message_to_summarize):
        template = """Following is a conversation between a human and a personalised health chat bot.

                    {text}

                    Summarize the conversation and don't loose any information while creating the summary

                    """

        prompt = PromptTemplate(
            input_variables=["text"], template=template
        )
        summary_chain = LLMChain(llm=ChatOpenAI(temperature=0, model_name="gpt-4o-mini"), prompt=prompt)
        summary = summary_chain.run(text=group_of_message_to_summarize)
        return summary
