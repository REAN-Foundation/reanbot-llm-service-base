from app.domain_types.schemas.llm_service import LlmChainParameters
from .personal_data_in_cache import PersonalDataCacheHandler
from app.common.document_utils import get_llm_document_path
from app.domain_types.schemas.personal_data_manager_interface import IPersonalDataManager
import pandas as pd

class PersonalData(IPersonalDataManager):

    def store_personal_data(self, client_name, llm_chain_parameters: LlmChainParameters):
        print("needs to be refactored for vector stores")
        # if llm_service_body.personalised_bot_object.personal_data_collection.file_type == "file":
        #     file = llm_service_body.personalised_bot_object.personal_data_collection.filename.split('.')
        #     document_path = get_llm_document_path(client_name, file[0], file[1])
        #     print("document_path",document_path)
        #     vector_db = create_load_vector_store(client_name, "user_personal_data", document_path)

    def retrieve_personal_data(self,user_id):
        print("needs to be refactored for vector stores")
        #Try to create vector_db as a class instance instead of passing the instance as function parameter
        # return vector_db.similarity_search(user_id, k=1)