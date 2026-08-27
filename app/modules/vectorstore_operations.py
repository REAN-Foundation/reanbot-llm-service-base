import os
from app.common.document_utils import get_llm_document_path, get_llm_chain_parameters
from app.modules.vectorstores.faiss import FaissVectorstore
from app.modules.document_loaders import DocumentLoader


class VectorStoreOperations():

    def __init__(self, client_name, project_name):
        self.client_name = client_name
        self.project_name = project_name
        self.document_loader = DocumentLoader()
        self.faiss_vectorstore = FaissVectorstore()

    def get_document_data(self, client_name, project_name):
        llm_chain_parameters = get_llm_chain_parameters(client_name, project_name)
        list_of_doc = llm_chain_parameters.doc_name
        list_of_doc_path = []
        for ele in list_of_doc:
            document_path = get_llm_document_path(self.client_name, self.project_name, ele, llm_chain_parameters.doc_type)
            list_of_doc_path.append(document_path)
        return self.document_loader.load_document(list_of_doc_path, llm_chain_parameters=llm_chain_parameters)


    def get_faiss_db(self, document_data):
        vectorstore_locations = self.faiss_vectorstore.local_vectorstore_location(self.client_name)
        index_name = self.faiss_vectorstore.client_index(self.client_name, self.project_name)

        if not os.path.exists(vectorstore_locations):
            os.makedirs(vectorstore_locations)

        vector_store = os.listdir(vectorstore_locations)
        matching_files = [filename for filename in vector_store if filename.split(".")[0] == index_name]

        if len(matching_files) == 0:
            faiss_db = self.faiss_vectorstore.load_vectorstore(document_data)
            self.faiss_vectorstore.save_db_local(faiss_db, self.client_name, self.project_name)
        else:
            faiss_db = self.faiss_vectorstore.load_local_vectorstore(self.client_name, self.project_name, index_name)

        return faiss_db

    def load_vectorstore_local(self, client_name, project_name):
        document_data = self.get_document_data(client_name, project_name)
        self.get_faiss_db(document_data)