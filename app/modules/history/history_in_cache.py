from app.domain_types.schemas.cache_datastore_interface import ICacheHandler
from app.modules.history.history_summerizer import Summerizer
from cachetools import TTLCache
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI

class HistoryCacheHandler(ICacheHandler):

    cache = TTLCache(maxsize=100, ttl=300)

    def get_cache(self, key):
        if key in self.cache:
            return self.cache[key]
        else:
            return "no conversation as of yet"

    def update_cache(self, user_id, data):
        summerizer = Summerizer()
        if user_id in self.cache:
            valid_history = self.valid_history_data(data)
            if (valid_history == "Response: valid"):
                # Retrieve the existing string from the cache
                existing_data = self.cache[user_id]
                word_count = self.counter(existing_data)
                # print("word count of human: ", word_count)
                if word_count > 5:
                    summary = summerizer.summerize(existing_data)
                    existing_data = summary
                # Concatenate the new data with the existing string
                updated_data = f"{existing_data}, {data}"
                # Store the updated string back in the cache
                self.cache[user_id] = updated_data
            else:
                pass
        else:
            # If the key does not exist, create a new entry with the data
            self.cache[user_id] = data

    def counter(self, existing_data):
        main_string = existing_data
        sub_string = "human:"
        count_er = 0
        start_index = 0
        for i in range(len(main_string)):
            j = main_string.find(sub_string, start_index)
            if j != -1:
                start_index = j + 1
                count_er += 1
        return count_er

    def valid_history_data(self, data_to_validate):
        template = """Given the following conversation between a human and a personalized health chatbot:

                    {text}

                    Determine whether the chatbot's response is within its scope. If the chatbot is unable to answer or refuses to answer any question saying it is not in its scope to answer, return "invalid". In other cases, return "valid".

                    Example conversation:

                    human: What is in week 7?
                    Chatbot: Week 7 covers healthy eating, providing information on reading food labels, cooking to lower cholesterol, and an understanding check.

                    Response: valid

                    Example conversation:

                    human: What is the best exercise for weight loss?
                    Chatbot: I'm sorry, but I cannot provide personalized exercise recommendations.

                    Response: invalid

                    """

        prompt = PromptTemplate(
            input_variables=["text"], template=template
        )
        valid_chain = LLMChain(llm=ChatOpenAI(temperature=0, model_name="gpt-4o-mini"), prompt=prompt)
        response = valid_chain.run(text=data_to_validate)
        return response
    
    def delete_cache(self, user_id):
        if user_id in self.cache:
            del self.cache[user_id]
            return True
        return False
    