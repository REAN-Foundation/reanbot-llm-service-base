from abc import ABC, abstractmethod
from app.domain_types.schemas.llm_service import LlmChainParameters

class ISummerizer(ABC):

    @abstractmethod
    def summerize(self, data_to_summarize):
        pass