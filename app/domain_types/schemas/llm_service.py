from pydantic import BaseModel, Field
from typing import Optional, List


class LlmServiceRequest(BaseModel):
    userID: str
    user_query: str
    tenant_display_code: Optional[str] = None
    tenant_id: Optional[str] = None
    patient_user_id: Optional[str] = None
    
class LlmServiceResponse(BaseModel):
    answer: str
    intent: str
    detected_language: str = Field(default='')
    source_of_info: str = Field(default='')
    similar_docs: List = Field(default=[])
    sensitivity_flag: str = Field(default='')


class PersonalDataCollection(BaseModel):
    file_type: str
    filename: Optional[str] = None
    data_store: str


class PersonalisedBotObject(BaseModel):
    personal_data_collection: PersonalDataCollection
    prompt_with_personalised_data: str
    prompt_template_input_variables_for_personalised_data: list


# personalised: Optional[bool] can be made required in future implementation
class LlmChainParameters(BaseModel):
    chunk_size: int
    chunk_overlap: int
    model_name: str
    prompt: str
    doc_type: str
    doc_name: list
    list_of_prompt_template_input_variables: list
    personalised_bot_object: Optional[PersonalisedBotObject] = None
    content_service: Optional[bool] = None
    sensitivity_check: Optional[bool] = None
    age_check: Optional[bool] = None

class LlmDataObject(BaseModel):
    similarity_search_docs: list
    user_query: str
    history: str
    personal_data: str
    personalised: bool
    llm_chain_parameters: LlmChainParameters

