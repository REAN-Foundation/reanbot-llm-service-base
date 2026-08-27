from app.domain_types.schemas.cache_datastore_interface import ICacheHandler
from .personal_data_summerizer import Summerizer
from cachetools import TTLCache

class PersonalDataCacheHandler(ICacheHandler):

    cache = TTLCache(maxsize=100, ttl=300)

    def get_cache(self, key):
        if key not in self.cache:
            print("error in key", key)
            raise KeyError(key)
        print("get data",self.cache[key])
        return self.cache[key]

    def update_cache(self, data):
        summarizer = Summerizer()
        for patient in data:
            patient_id = patient['user_id']
            if patient_id not in self.cache:
                summary = summarizer.summerize(patient)
                self.cache[patient_id] = summary
            else:
                print("data exists")
                pass
