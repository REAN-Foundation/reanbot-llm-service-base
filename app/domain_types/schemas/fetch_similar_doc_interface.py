from abc import ABC, abstractmethod

class ISimilarDocFetcher(ABC):

    @abstractmethod
    def fetch_similar_docs(self, user_query,client_name,project_name):
        pass