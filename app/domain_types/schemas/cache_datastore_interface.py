from abc import ABC, abstractmethod
import pickle
from cachetools import TTLCache

class ICacheHandler(ABC):
    cache = TTLCache(maxsize=100, ttl=300)

    @abstractmethod
    def get_cache(self, key):
        pass

    @abstractmethod
    def update_cache(self, data):
        pass

    def serialize_cache(self, file_path):
        with open(file_path, 'wb') as f:
            pickle.dump(self.cache, f)

    def deserialize_cache(self, file_path):
        with open(file_path, 'rb') as f:
            self.cache = pickle.load(f)