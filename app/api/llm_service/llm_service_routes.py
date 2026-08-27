import os

from fastapi import APIRouter, Depends, status, BackgroundTasks, HTTPException
from app.domain_types.schemas.llm_service import LlmServiceRequest
from app.api.llm_service.run_llm_chain import RunLLMChain
from app.modules.llm_request_processor import LLMRequestProcessor
from app.modules.history.history_in_cache import HistoryCacheHandler
from app.modules.vectorstore_operations import VectorStoreOperations
from app.modules.analyrics.analytics_service import AnalyticsService

#######################################################

router = APIRouter(
    prefix="/llm_service",
    dependencies=[],
    responses={404: {"description": "Not found"}},
)

@router.post("/{client_name}/{project_name}")
async def llm_service(client_name: str, project_name: str, request_body: LlmServiceRequest, background_tasks: BackgroundTasks):
    llm_request_processor = LLMRequestProcessor()
    chain_data = llm_request_processor.process_request(client_name, project_name, request_body)
    llm_chain = RunLLMChain()
    data = llm_chain.run_chain(chain_data,client_name, project_name, request_body)
    if data is not None and 'response' in data and 'cache_data' in data:
        if "analytics_event" in data:
            background_tasks.add_task(
                AnalyticsService.push_event,
                data["analytics_event"]
            )
        cache_handler_obj = HistoryCacheHandler()
        cache_handler_obj.update_cache((request_body.userID + '_' + client_name), f"human: {request_body.user_query}, Chatbot: {data['cache_data']}")
        return data["response"]
    else:
        default_response = "Regrettably, I encountered challenges in handling your request. I encourage you to rephrase your query or pose an alternative question for further assistance."
        cache_handler_obj = HistoryCacheHandler()
        cache_handler_obj.update_cache((request_body.userID + '_' + client_name), f"human: {request_body.user_query}, Chatbot: {default_response}")
        return default_response

@router.post("/vectorstore/{client_name}/{project_name}")
async def create_vectorstore(client_name: str, project_name: str, background_tasks: BackgroundTasks):
    vectorstores = VectorStoreOperations(client_name, project_name)
    background_tasks.add_task(vectorstores.load_vectorstore_local, client_name, project_name)

@router.delete("/cache/{client_name}/{user_id}")
async def delete_user_cache(client_name: str, user_id: str):
    cache_handler = HistoryCacheHandler()

    user_id = user_id.replace("+", "").replace("-", "")
    cache_key = f"{user_id}_{client_name}"
    print(f"Attempting to delete cache for key: {cache_key}")

    is_deleted = cache_handler.delete_cache(cache_key)

    if is_deleted:
        return {"message": "User cache deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="User cache not found")
