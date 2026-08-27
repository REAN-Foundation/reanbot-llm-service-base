##-------------------------------------- Obsolete -----------------------------------##
import os
from app.modules.document_loaders import DocumentLoader
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from app.modules.vectorstores.milvus import MilvusVectorstore
from app.domain_types.schemas.llm_service import LlmChainParameters
from app.common.document_utils import read_config_json, get_llm_document_path
from app.modules.vectorstores.faiss import FaissVectorstore

class FetchDocument:

    def __init__(self):
        self.document_loader = DocumentLoader()

    def fetch_tags_from_query(self, user_query: str):
        tag_document = os.path.join(os.getcwd(), f'tags.csv')
        # document_loader = DocumentLoader()
        tag_document_data = self.document_loader.csv_document_loader(tag_document, source_column='text', metadata_columns=['document'])
        tag_template = """
            I want to retrieve a keyword relevant to what the user has asked.
            Summarize the user query as the most relevant keywords and return an array of strings.

            For example if the query is "What are the symptoms of diabetes?", the keyword is "Diabetes symptoms".  

            The user query is:
            {user_query}

            The keyword is:
        """

        tag_prompt = PromptTemplate(
            input_variables=["user_query"],
            template=tag_template
        )
        tag_chain = tag_prompt | ChatOpenAI(temperature=0, model_name="gpt-4o-mini")
        tag_ans = tag_chain.invoke({"user_query": user_query})
        print(tag_ans.content)
        milvus_vector_store = MilvusVectorstore()
        tag_vector_db = milvus_vector_store.load_vectorstore(tag_document_data, client_name="tags", project_name="keywords")
        relevant_docs_names = tag_vector_db.similarity_search_with_score(tag_ans.content)
        tags = [tup for tup in relevant_docs_names if tup[1] <= 0.30]
        print(tags)
        return tags
    
    def get_similar_docs(self,user_query:str,client_name,project_name):
        configs = read_config_json(client_name, project_name)
        llm_chain_parameters = LlmChainParameters(**configs)
        tags = self.fetch_tags_from_query(user_query)
        similar_docs = []
        faiss = FaissVectorstore()
        for tag in tags:
            print(tag[0].metadata)
            filenames = tag[0].metadata['document'].split('.')
            document_path = get_llm_document_path(client_name, project_name, filenames[1], filenames[0])
            if not os.path.exists(document_path):
                document_path = os.path.join(os.getcwd(), 'app', 'api', 'llm_service', 'data_files', 'general', 'general.txt')
                llm_chain_parameters.doc_type = 'txt'
            document_data = self.document_loader.load_document(document_path,llm_chain_parameters=llm_chain_parameters)
            vectorstore_locations = faiss.local_vectorstore_location(client_name)
            index_name = faiss.client_index(client_name,project_name)
            if not os.path.exists(vectorstore_locations):
                os.makedirs(vectorstore_locations)
            vector_store = os.listdir(vectorstore_locations)
            matching_files = [filename for filename in vector_store if filename.startswith(index_name)]
            if len(matching_files) == 0:
                faiss_db = faiss.load_vectorstore(document_data)
                faiss.save_db_local(faiss_db,client_name,project_name)
            else:
                faiss_db = faiss.load_local_vectorstore(client_name,project_name)

            similarity_search = faiss_db.similarity_search_with_score(user_query, k=3)
            filtered_docs = [tup for tup in similarity_search if tup[1] <= 0.30]
            for doc in filtered_docs:
                similar_docs.append(doc[0].page_content)

        # print("similar_docs",similar_docs)
        return similar_docs