import os
import requests

from app.modules.document_loaders import DocumentLoader
from app.domain_types.schemas.llm_service import LlmServiceRequest, LlmChainParameters
from app.modules.history.history_in_cache import HistoryCacheHandler
from app.common.document_utils import read_config_json
from app.modules.personal_data.personal_data_manager_cache import PersonalDataManagerCache
from app.modules.fetch_filtered_document import FetchDocument
from app.modules.similar_document.similar_doc_via_tag import TagBasedSimilarDoc
from app.modules.similar_document.all_client_specific_doc import ClientDocs

class LLMRequestProcessor:
    def __init__(self):
        self.document_loader = DocumentLoader()

    def get_similar_docs(self, client_name: str, request_body: LlmServiceRequest, endpoint: str):
        try:
            query = request_body.user_query
            if "||" in query:
                query = query.split("||", 1)[1].strip()

            payload = {
                #"TenantId": client_name,
                "TenantId": request_body.tenant_display_code,
                "Query": query
            }

            headers = {
                "Content-Type": "application/json"
            }

            response = requests.post(endpoint, json=payload, headers=headers)
            response = response.json()
            response_data = response["Message"]

            if response["HttpCode"] == 200:
                return response_data
            else:
                return None
        except Exception as e:
            print(e)


    def process_request(self, client_name: str, project_name: str, request_body: LlmServiceRequest):
        try:
            # Getting the document data should be done in middleware
            configs = read_config_json(client_name, project_name)
            llm_chain_parameters = LlmChainParameters(**configs)

            if llm_chain_parameters.content_service:
                # implementation for new bot content service
                content_service_base_url = os.environ["BOT_CONTENT_SERVICE_ENDPOINT"]
                content_service_endpoint =  f"{content_service_base_url}/vectorstore/similarity-search"
                fetched_similar_docs = self.get_similar_docs(client_name, request_body, content_service_endpoint)
                if not fetched_similar_docs:
                    fetch = TagBasedSimilarDoc(client_name, project_name)
                    similar_docs = fetch.fetch_similar_docs(request_body.user_query)

                    if not similar_docs:
                        fetch = ClientDocs(client_name, project_name)
                        similar_docs = fetch.fetch_similar_docs(request_body.user_query)
                else:
                    similar_docs = fetched_similar_docs
            else:
                # relevant_docs = vector_db.similarity_search(request_body.user_query)
                fetch = TagBasedSimilarDoc(client_name, project_name)
                similar_docs = fetch.fetch_similar_docs(request_body.user_query)

                if not similar_docs:
                    fetch = ClientDocs(client_name, project_name)
                    similar_docs = fetch.fetch_similar_docs(request_body.user_query)

            # Personal data
            if(llm_chain_parameters.personalised_bot_object and llm_chain_parameters.personalised_bot_object.personal_data_collection.data_store == "vectorstore"):
                # get personal data from vector store manager
                pass
            elif(llm_chain_parameters.personalised_bot_object and llm_chain_parameters.personalised_bot_object.personal_data_collection.data_store == "cache"):
                personal_data_instance = PersonalDataManagerCache()
                # the storing of the personal data should be moved to higher level
                personal_data_instance.store_personal_data(client_name, llm_chain_parameters.personalised_bot_object.personal_data_collection)
                personal_data = personal_data_instance.retrieve_personal_data(request_body.userID)
            else:
                personal_data=""
            cache_handler_obj = HistoryCacheHandler()
            cached_history = cache_handler_obj.get_cache((request_body.userID + '_' + client_name))

            # data = {
            #     "similarity_search_docs": similar_docs,
            #     "user_query": request_body.user_query,
            #     "history": cached_history,  
            #     "personal_data": personal_data,
            #     "personalised": hasattr(llm_chain_parameters, 'personalised_bot_object') and llm_chain_parameters.personalised_bot_object is not None,
            #     "llm_chain_parameters": llm_chain_parameters
            # }
            data = LLMDataContainer(
                similar_docs,
                request_body.user_query,
                cached_history,
                personal_data,
                hasattr(llm_chain_parameters, 'personalised_bot_object') and llm_chain_parameters.personalised_bot_object is not None,
                llm_chain_parameters,
                request_body.tenant_display_code
            )
            return data
        except Exception as e:
            print(e)

class LLMDataContainer:
    def __init__(self, similarity_search_docs, user_query, history, personal_data, personalised, llm_chain_parameters, tenant_display_code):
        self.similarity_search_docs = similarity_search_docs
        self.user_query = user_query
        self.history = history
        self.personal_data = personal_data
        self.personalised = personalised
        self.llm_chain_parameters = llm_chain_parameters
        self.tenant_display_code = tenant_display_code