import os
from app.domain_types.schemas.vectorestore_interface import IVectorstore
from langchain_openai import OpenAIEmbeddings
from pymilvus import connections, Collection, utility
from langchain_community.vectorstores import Milvus

class MilvusVectorstore(IVectorstore):

    def create_db_connection(self):
        connections.connect("default",
                            uri=os.environ.get("MILVUS_URI"),
                            token=os.environ.get('MILVUS_TOKEN')
                            )

    def disconnect_db(self,alias):
        connections.disconnect(alias)

    def create_collection(self,client_name, project_name,schema):
        collection_name = f"{client_name}_{project_name}"
        collection = Collection(
            name=collection_name,
            schema=schema,
            using='default',
            shards_num=2
            )
        return collection
    
    def insert_data_in_collection(self,collection_name,data):
        collection = Collection(collection_name)      # Get an existing collection.
        collection.insert(data)

    def client_index(self, client_name, project_name):
        index_params = {
            "metric_type":"L2",
            "index_type":"IVF_FLAT",
            "params":{"nlist":1024}
        }
        collection = Collection("book")      
        collection.create_index(
            field_name="book_intro", 
            index_params=index_params
        )
    
    def load_vectorstore(self, documents, **kwargs):
        self.create_db_connection()
        embeddings = self.embedding_model()
        client_name = kwargs.get("client_name",None)
        project_name = kwargs.get("project_name",None)
        collection_name = f"{client_name}_{project_name}"
        connection_args = {
            "uri": os.environ.get("MILVUS_URI"),
            "token": os.environ.get("MILVUS_TOKEN")
        }
        check_collection = utility.has_collection(collection_name)
        if check_collection:
            print('Milvus collection exists')
            vector_db = Milvus(embeddings,
                            connection_args=connection_args,
                            collection_name=collection_name
                            )
        else:
            print('Creating Milvus collection')
            vector_db = Milvus.from_documents(
                documents,
                embeddings,
                connection_args=connection_args,
                collection_name=collection_name
            )
        return vector_db

    def similarity_search(self,vector_db,user_query):
        similar_docs = vector_db.similarity_search(user_query)
        return similar_docs
    
    def embedding_model(self, model='text-embedding-ada-002'):
        embedding_model = OpenAIEmbeddings(model=model)
        return embedding_model
    
    def handle_file_types(self):
        pass

    def load_local_vectorstore(self):
        pass

    def local_vectorstore_location(self):
        pass

    def update_doc(self):
        pass