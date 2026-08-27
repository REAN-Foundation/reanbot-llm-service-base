import os
from app.domain_types.schemas.vectorestore_interface import IVectorstore
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import openai
import math


class FaissVectorstore(IVectorstore):

    def load_vectorstore(self,documents):
        try:
            embedding_model = self.embedding_model()
            db = FAISS.from_documents(documents, embedding_model)
            return db
        except Exception as e:
            print("UNABLE TO CREATE VECTORSTORE FROM DOCS", e)
            embeddings = self.create_embeddings(documents)
            embedding_model = self.embedding_model()
            db = FAISS.from_embeddings(embeddings, embedding_model)
            return db

    def load_local_vectorstore(self,client_name,project_name, index_name=False):
        embedding_model = self.embedding_model()
        if not index_name:
            index_name = self.client_index(client_name,project_name)
        local_vectorstore = self.local_vectorstore_location(client_name)
        db = FAISS.load_local(folder_path=local_vectorstore, index_name=index_name, embeddings=embedding_model, allow_dangerous_deserialization=True)
        return db

    def save_db_local(self, db, client_name, project_name, index_name=False):
        if not index_name:
            index_name = self.client_index(client_name, project_name)
        local_vectorstore = self.local_vectorstore_location(client_name)
        db.save_local(folder_path=local_vectorstore, index_name=index_name)
        
    def similarity_search(self,vector_db,user_query):
        similar_docs = vector_db.similarity_search(user_query)
        return similar_docs
    
    def embedding_model(self, model='text-embedding-ada-002'):
        embedding_model = OpenAIEmbeddings(model=model)
        return embedding_model
    
    def handle_file_types():
        pass

    def local_vectorstore_location(self,client_name):
        vectorstore_locations = os.path.join(
            os.getcwd(),
            'app',
            'vector_stores',
            client_name
        )
        return vectorstore_locations
    
    def client_index(self,client_name,project_name):
        return f"{client_name}_{project_name}"
    
    def update_doc():
        pass

    def create_db_connection(self):
        pass

    def disconnect_db(self):
        pass

    def create_collection(self):
        pass
    
    def insert_data_in_collection(self):
        pass

    def create_embeddings(self, documents):
        try:
            print("Creating embeddings from documents directly")

            # Read batch size from env or default to 100
            batch_size = int(os.environ.get("EMBED_BATCH_SIZE", 100))

            embedding_array = []
            texts = [doc.page_content for doc in documents]
            num_calls = math.ceil(len(texts) / batch_size)
            print(f"WILL BE PROCESSING {len(texts)} TEXTS IN {num_calls} OPEN AI EMBEDDINGS CALLS")
            for i in range(0, len(documents), batch_size):
                batch = texts[i:i+batch_size]
                embeddings = self.embed_batch(batch)
                embedding_array.extend(zip(batch, embeddings))
            return embedding_array

            ### TO BE REMOVED LATER
            # for doc in documents:
            #     try:
            #         result = openai.embeddings.create(
            #             input=doc.page_content,
            #             model="text-embedding-ada-002"
            #         )
            #         embedding_array.append((doc.page_content, result.data[0].embedding))
            #     except Exception as e:
            #         print("FAILED TO CREATE EMBEDDING MANUALLY FOR DOCUMENT")
            #         print(e, doc)
            # return embedding_array
        except Exception as e:
            print("FAILED TO CREATE EMBEDDING MANUALLY", e)

    def embed_batch(self, batch):
        response = openai.embeddings.create(
            model="text-embedding-ada-002",
            input= batch
        )
        return [r.embedding for r in response.data]