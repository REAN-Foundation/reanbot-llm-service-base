from datetime import datetime, timezone
import json
import os
import requests
import pandas as pd
from langchain_core.prompts import ChatPromptTemplate

from app.domain_types.schemas.llm_service import LlmServiceResponse
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from app.modules.document_loaders import DocumentLoader
from app.domain_types.schemas.llm_service import LlmDataObject, LlmChainParameters
from langchain.chains import LLMChain
from app.common.document_utils import read_config_json


class RunLLMChain:
    def __init__(self):
        self.document_loader = DocumentLoader()

    def initialize_chat_model(self, model_name, temperature=0):
        """
        Dynamically initialize ChatOpenAI model with error handling and fallback options.
        Handles models that don't support temperature=0 and applies appropriate parameters.
        """
        # Models that don't support temperature=0 (only support default value of 1)
        models_without_temperature_support = ["gpt-5", "gpt-5-mini"]

        # Check if the model doesn't support temperature adjustment
        model_lower = model_name.lower()
        if any(unsupported in model_lower for unsupported in models_without_temperature_support):
            print(f"Model {model_name} doesn't support temperature=0, using default temperature")
            try:
                # For GPT-5 models, include reasoning_effort parameter but no temperature
                if "gpt-5" in model_lower:
                    llm = ChatOpenAI(
                        model=model_name,
                        reasoning_effort="low"
                    )
                else:
                    # For other models (o3, o4-mini, etc.), don't include temperature or reasoning_effort
                    llm = ChatOpenAI(model=model_name)
                return llm
            except Exception as e:
                print(f"Error initializing model {model_name}: {e}")
                return self._fallback_to_supported_model()

        # Models that support temperature adjustment
        try:
            # For other models (gpt-4, gpt-3.5, etc.), use temperature but no reasoning_effort
            llm = ChatOpenAI(
                model=model_name,
                temperature=temperature
            )
            return llm
        except Exception as e:
            print(f"Error initializing model {model_name}: {e}")
            return self._fallback_to_supported_model()

    def _fallback_to_supported_model(self):
        """
        Fallback to a model that definitely supports temperature=0
        """
        try:
            print(f"Falling back to gpt-4o-mini (supports temperature=0)")
            return ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0
            )
        except Exception as fallback_error:
            print(f"Fallback model also failed: {fallback_error}")
            # Last resort - use default temperature
            try:
                print(f"Using gpt-4o-mini with default temperature")
                return ChatOpenAI(model="gpt-4o-mini")
            except Exception as final_error:
                print(f"All fallback attempts failed: {final_error}")
                return None

    def run_chain(self, data: LlmDataObject, client_name, project_name, request_body):
        try:
            configs = read_config_json(client_name, project_name)
            llm_chain_parameters = LlmChainParameters(**configs)
            age_check = llm_chain_parameters.age_check
            ans = None
            if age_check:
                underage_flag = self.check_underage_self_declaration(data.user_query)
                if underage_flag:
                    ans = self.run_restriction_chain()
            if ans is None:
                if (len(data.similarity_search_docs) > 0):
                    if data.personalised:
                        ans = self.run_personalized_chain(data)
                    else:
                        ans = self.run_default_chain(data, request_body)
                else:
                    ans = self.run_fallback_chain(data)

            try:
                response = LlmServiceResponse(**json.loads(ans))
                configs = read_config_json(client_name, project_name)
                llm_chain_parameters = LlmChainParameters(**configs)
                if llm_chain_parameters.sensitivity_check:
                    response.sensitivity_flag = self.extract_sensitivity_flag(response.answer)
                cache_data = response.answer
                translated_response = self.run_translation(response.answer, response.detected_language)
                response.answer = translated_response
            except Exception as e:
                print("LLM did not return a json")
                extracted_ans = self.extract_answer(ans)
                if llm_chain_parameters.sensitivity_check:
                    sensitivity_flag = self.extract_sensitivity_flag(extracted_ans)
                else:
                    sensitivity_flag = ""
                response_json = {
                    "answer": extracted_ans,
                    "detected_language": "",
                    "intent": "",
                    "source_of_info": "",
                    "sensitivity_flag": sensitivity_flag
                }
                response = LlmServiceResponse(**response_json)
                cache_data = extracted_ans
                translated_response = self.run_translation(response.answer, response.detected_language)
                response.answer = translated_response

            question_only = self.extract_user_question(data.user_query)
            event = {
                "UserId": request_body.patient_user_id,
                "TenantId": request_body.tenant_id or None,
                "SessionId": None,
                "ResourceId": None,
                "ResourceType": "llm-response",
                "SourceName": request_body.tenant_display_code,
                "SourceVersion": None,
                "EventName": "ChatMessage",
                "EventSubject": "LLMConversation",
                "EventCategory": "UserChat",
                "ActionType": "system-action",
                "ActionStatement": f"LLM answered question for user '{request_body.userID}'.",
                "Timestamp": datetime.now(timezone.utc).isoformat(),
                "Attributes": {
                    "Question": question_only,
                    "Answer": response.answer
                }
            }

            if len(data.similarity_search_docs) > 0:
                if type(data.similarity_search_docs[0]) is str:
                    response.similar_docs = [context for context in data.similarity_search_docs]
                else:
                    response.similar_docs = [context["pageContent"] for context in data.similarity_search_docs]
            return {"response": response, "cache_data": cache_data, "analytics_event": event}
        except Exception as e:
            print(e)

    def run_personalized_chain(self, data: LlmDataObject):
        list_of_input_variables = data.llm_chain_parameters.personalised_bot_object.prompt_template_input_variables_for_personalised_data
        prompt = PromptTemplate(
            input_variables=list_of_input_variables,
            template=data.llm_chain_parameters.personalised_bot_object.prompt_with_personalised_data
        )
        llm = self.initialize_chat_model(data.llm_chain_parameters.model_name, temperature=0)
        if llm is None:
            raise Exception("Failed to initialize LLM model")

        formatted_prompt = prompt.format(
            input_documents=data.similarity_search_docs,
            personal_data=data.personal_data,
            chat_history=data.history,
            human_input=data.user_query
        )
        return llm.invoke(formatted_prompt).content

    def run_default_chain(self, data: LlmDataObject, request_body):
        content_service_base_url = os.environ["BOT_CONTENT_SERVICE_ENDPOINT"]
        content_service_endpoint = f"{content_service_base_url}/llm-prompts/search"

        payload = {
            "isActive": "true",
            "tenantId": request_body.tenant_id or None,
        }

        headers = {
            "Content-Type": "application/json"
        }

        response = requests.get(content_service_endpoint, params=payload, headers=headers)
        response = response.json()
        response_data = response["Data"]

        if response_data["TotalCount"] == 0:
            list_of_input_variables = data.llm_chain_parameters.list_of_prompt_template_input_variables
            prompt_template = data.llm_chain_parameters.prompt
        else:
            list_of_input_variables = response_data["Items"][0]["Variables"]
            prompt_template = response_data["Items"][0]["Prompt"]
        # list_of_input_variables = data.llm_chain_parameters.list_of_prompt_template_input_variables
        prompt = PromptTemplate(
            input_variables=list_of_input_variables, template=prompt_template
        )
        llm = self.initialize_chat_model(data.llm_chain_parameters.model_name, temperature=0)
        if llm is None:
            raise Exception("Failed to initialize LLM model")

        formatted_prompt = prompt.format(
            input_documents=data.similarity_search_docs,
            chat_history=data.history,
            human_input=data.user_query
        )
        return llm.invoke(formatted_prompt).content

    def run_fallback_chain(self, data: LlmDataObject):
        list_of_input_variables = data.llm_chain_parameters.list_of_prompt_template_input_variables
        prompt = 'You are a chatbot concerned with medical health related queries only. First detect the language in which the query is received and answer in the same language.\n Use the following json when the user is greeting or asking how the bot works. {{"answer": "Hello and welcome! I am here to provide reliable information about a wide range of diseases. Whether you are looking for details on symptoms, treatments, prevention, or general insights, I am here to help.","intent": "Greetings","detected_language": "","source_of_info": }}\n If the user is trying to have a small talk or giving a feedback, acknowledge them, provide an intelligent reply and guide them back to ask questions relevant to your context. Do not use the greeting message as a reply here. Use the following JSON structure\n {{"answer": ,"intent": "Small Talk" ,"detected_language": "","source_of_info": }} \'\n if the question is relevant to medical health then provide the following json.\n {{"answer": "\'your answer\'. \'This answer is not verified by our experts\'","intent":  "Document not found","detected_language": "","source_of_info": }}. Always append \'This answer is not verified by our experts\' to the answer. \n If the question is out of the context of medical health and even if there are input documents then provide the following json.\n {{"answer": "This topic is out of context for medical health. Please feel free to ask any questions relevant to medical health.","intent":  "Fallback Intent","detected_language": "","source_of_info": }}\n Also provide the source of the information in the above json formats as a string.\n Use one of the following to describe the source, if it is not relevant provide the original source of the information.\n ["Provided Documents","Training Data", "Internet"]\n Strictly adhere to the json structure of the above mentioned format for all responses.\n The values to the respective keys in the json must be string. If there is an empty value give an empty string.\n This is chat history for your context. Always consider both chat history and user\'s health profile to be able to grasp precise situation user is in and then respond accordingly\n {chat_history}\n Human: {human_input} Chatbot:'
        prompt = PromptTemplate(
            input_variables=list_of_input_variables, template=prompt
        )
        llm = self.initialize_chat_model("gpt-4o-mini", temperature=0)
        if llm is None:
            raise Exception("Failed to initialize LLM model")

        formatted_prompt = prompt.format(
            input_documents=data.similarity_search_docs,
            chat_history=data.history,
            human_input=data.user_query
        )
        return llm.invoke(formatted_prompt).content
    
    def run_restriction_chain(self):
        restriction_message = (
            "WE ARE SORRY BUT WE CANNOT PROVIDE SEXUAL HEALTH ADVICE TO USERS WHO ARE 18 YEARS OR YOUNGER. "
            "IF YOU HAVE GENERAL QUESTIONS ABOUT GROWING UP OR BODY CHANGES, YOU MAY CONSIDER SPEAKING WITH "
            "A TRUSTED ADULT, PARENT, GUARDIAN OR A HEALTHCARE PROVIDER."
        )

        response_json = {
            "answer": restriction_message,
            "intent": "Age Restriction",
            "detected_language": "en",
            "source_of_info": ""
        }

        return json.dumps(response_json)

    def extract_user_age(self, user_query: str):
        try:
            if "User information:" not in user_query:
                return None
            user_info_part = user_query.split("||")[0]
            json_str = user_info_part.split("User information:")[1].strip()

            if json_str == "{}":
                return None

            user_info = json.loads(json_str)

            age = user_info.get("age")

            if isinstance(age, int):
                return age

            if isinstance(age, str) and age.isdigit():
                return int(age)

            return None

        except Exception:
            return None
        
    def extract_user_question(self, user_query: str) -> str:
        try:
            if "||" in user_query:
                question_part = user_query.split("||")[1]
                question_part = question_part.replace("User Question:", "")
                question_part = question_part.replace("USER QUESTION:", "")
                question_part = question_part.strip()

                return question_part

            return user_query.strip()

        except Exception:
            return user_query.strip()
        
    def check_underage_self_declaration(self, user_query: str) -> bool:
        question = self.extract_user_question(user_query)

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        prompt = ChatPromptTemplate.from_messages([
            ("system",
            "You are an age classification system.\n"
            "Analyze the user's message and determine:\n"
            "1. If the user explicitly states they are below 18 years old.\n"
            "2. If the user explicitly states they are 18 years old or above.\n"
            "3. If the message does not mention age.\n\n"
            "Respond with ONLY one of these exact words:\n"
            "UNDERAGE\n"
            "ADULT\n"
            "NO_AGE_MENTION\n"
            "Do not explain anything."
            ),
            ("human", "{text}")
        ])

        chain = prompt | llm
        result = chain.invoke({"text": question}).content.strip()

        if result == "UNDERAGE":
            return True

        return False

    def extract_answer(self, input_string):
        answer_start = input_string.find('"answer":') + len('"answer":')
        answer_end = input_string.find('"intent"', answer_start + 1)
        answer = input_string[answer_start:answer_end]
        return answer
    
    def extract_sensitivity_flag(self, text_to_classify):
        template = """
        You are given a text response that was provided to a user.

        Your task is to analyze the response and classify its sensitivity level based on the following rules:

        - Critical / Urgent: Sexual violence and abuse (rape, assault, child sexual abuse, trafficking, grooming), 
        mental health crisis (suicidal thoughts, self-harm, severe trauma), unsafe abortion or pregnancy crisis, 
        immediate risk to child pregnancy, medical emergencies, consent violations with minors, 
        forced conversion therapy or corrective rape or imminent violence against LGBTQ+ individuals, 
        FGM threat or unsafe procedure, child pornography, forced nudity or demand for nudity.

        - High Sensitivity: Unintended pregnancy distress (without immediate health risk), partner coercion, 
        STI or HIV disclosure with stigma or violence risk, fear of being outed, revenge porn or non-consensual image sharing, 
        ongoing intimate partner violence (non-lethal), severe anxiety or depression or shame linked to sexual or reproductive health, 
        misinformation with harmful health consequences (but not yet life-threatening).

        - Sensitive but Safe: Contraception worries, curiosity about age of consent laws or sexual rights, 
        relationship pressure or emotional distress, general stigma-related concerns, 
        LGBTQ+ identity exploration without immediate safety threats, 
        normal adolescent questions about puberty, masturbation, or body changes.

        If the response does not fall into any of these categories, return:
        Not sensitive

        Return your answer as one of these exact strings only:
        Critical / Urgent
        High Sensitivity
        Sensitive but Safe
        Not sensitive

        Response to classify:
        {text}
        """

        prompt = PromptTemplate(
            input_variables=["text"], template=template
        )
        sensitivity_chain = LLMChain(
            llm=ChatOpenAI(temperature=0, model_name="gpt-4o-mini"),
            prompt=prompt
        )
        response = sensitivity_chain.run(text=text_to_classify)
        return response.strip()

    def run_translation(self, message: str, expected_language: str):
        detected_language = self.detect_response_language(message)
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        if detected_language == "":
            detected_language = self.detect_response_language(message)

        if detected_language.lower() != expected_language.lower():
            translate_prompt = ChatPromptTemplate.from_messages([
                ("system",f"You are an expert at language translations.You are job is to translate the text into the language or the associated language code which is: {expected_language}. \\n\\n Translate the message as is do not add or remove or change anything. In case the {detected_language} is mixed, make sure the words from the other language get translated into the {expected_language}. ALWAYS MAKE SURE ALL THE WORDS IN A SENTENCE ARE TRANSLATED, THERE SHOULD NOT BE A MIX OF 2 DIFFERENT LANGUAGES AS MUCH AS POSSIBLE \\n Do not add any html tags for example '\\n' '\\t' etc. or any other formatting in the translation. Do not use markdown style and special symbols like hyphens or separators. Provide only a string."),
                ("human", "{text}")
            ])
            translate_chain = translate_prompt | llm
            translated = translate_chain.invoke({"text": message})
            return translated.content.strip()
        else:
            return message

    def detect_response_language(self, text: str) -> str:

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        detect_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a language detection model. Always respond with only the language name in english. Note the message could be hindi but typed in english, in such a case say Hinglish. If the text contains mixing or code switching for example, hindi devnagri mixed with english then say Mixed. Same is relevant for other languages typed in english."),
            ("human", "Detect the language of the following text: \n\n{text}")
        ])
        chain = detect_prompt | llm
        response = chain.invoke({"text": text})
        return response.content.strip()
