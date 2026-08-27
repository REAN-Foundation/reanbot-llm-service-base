import json
import os
from app.domain_types.schemas.llm_service import LlmChainParameters


def read_config_json(client_name: str,project_name: str):
    file_path = os.path.join(
        os.getcwd(),
        "app",
        "api",
        "llm_service",
        "data_files",
        client_name,
        project_name,
        f"{project_name}.json"
    )
    f = open(file_path)
    read_json = json.load(f)
    f.close()
    return read_json


def get_llm_document_path(client_name: str, project_name: str, doc_name: str = '', doc_type: str=''):
    file_path = os.path.join(
        os.getcwd(),
        "app",
        "api",
        "llm_service",
        "data_files",
        client_name,
        project_name,
        f"{project_name}_{doc_name}.{doc_type}"
    )
    return file_path

def get_llm_chain_parameters(client_name: str, project_name: str):
    configs = read_config_json(client_name, project_name)
    return LlmChainParameters(**configs)
