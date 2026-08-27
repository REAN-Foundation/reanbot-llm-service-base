from app.domain_types.schemas.llm_service import PersonalDataCollection
from .personal_data_in_cache import PersonalDataCacheHandler
from app.common.document_utils import get_llm_document_path
from app.domain_types.schemas.personal_data_manager_interface import IPersonalDataManager
import pandas as pd

class PersonalDataManagerCache(IPersonalDataManager):

    def store_personal_data(self, client_name, personal_data_collection: PersonalDataCollection):
        if personal_data_collection.file_type == 'file':
            file = personal_data_collection.filename.split('.')
            document_path = get_llm_document_path(client_name, file[0], file[1])
            csv_data_frame = pd.read_csv(document_path)
            personal_data_cache_handler = PersonalDataCacheHandler()
            personal_data_cache_handler.update_cache(csv_data_frame.to_dict(orient='records'))
        else:
            # handle other personal data stores such as databases/ getting data via api
            pass

    def retrieve_personal_data(self,user_id):
        personal_data_cache_handler = PersonalDataCacheHandler()
        return personal_data_cache_handler.get_cache(user_id)