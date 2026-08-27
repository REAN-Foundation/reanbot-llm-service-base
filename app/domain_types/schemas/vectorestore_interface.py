from abc import ABC, abstractmethod

class IVectorstore(ABC):

    @abstractmethod
    def create_db_connection(self,host,port,**kwargs):
        pass

    @abstractmethod
    def disconnect_db(self,alias,**kwargs):
        pass

    @abstractmethod
    def create_collection(self,client_name, project_name,schema,**kwargs):
        pass

    @abstractmethod
    def insert_data_in_collection(self,collection_name,data,**kwargs):
        pass

    @abstractmethod
    def load_vectorstore(self,documents,**kwargs):
        pass
    
    @abstractmethod
    def load_local_vectorstore(self,client_name,project_name,**kwargs):
        pass

    @abstractmethod
    def similarity_search(self,vector_db,user_query,**kwargs):
        pass

    @abstractmethod
    def embedding_model(self,model,**kwargs):
        pass

    @abstractmethod
    def handle_file_types(self):
        pass

    @abstractmethod
    def client_index(client_name,project_name,**kwargs):
        pass
    
    @abstractmethod
    def local_vectorstore_location(self,client_name,**kwargs):
        pass

    @abstractmethod
    def update_doc(self):
        pass