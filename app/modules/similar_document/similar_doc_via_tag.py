from app.domain_types.schemas.fetch_similar_doc_interface import ISimilarDocFetcher
import os
from app.modules.document_loaders import DocumentLoader
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from app.modules.vectorstores.milvus import MilvusVectorstore
from app.domain_types.schemas.llm_service import LlmChainParameters
from app.common.document_utils import read_config_json, get_llm_document_path
from app.modules.vectorstores.faiss import FaissVectorstore
from app.common.vectorstore_fallback_utils import create_tag_vectorstore_with_fallback

class TagBasedSimilarDoc(ISimilarDocFetcher):
    def __init__(self,client_name,project_name):
        self.client_name = client_name
        self.project_name = project_name
        self.document_loader = DocumentLoader()
        self.faiss_vectorstore = FaissVectorstore()
        self.milvus_vector_store = MilvusVectorstore()

    def fetch_tags_from_query(self, user_query: str):
        tag_document = os.path.join(os.getcwd(), 'tags.csv')
        tag_document_data = self.document_loader.csv_document_loader([tag_document], source_column='text', metadata_columns=['document'])
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

        # Try Milvus first, fallback to FAISS if connection fails or credentials missing
        tag_vector_db, is_milvus = create_tag_vectorstore_with_fallback(
            self.milvus_vector_store,
            self.faiss_vectorstore,
            tag_document_data,
            client_name="tags",
            project_name="keywords"
        )

        if not is_milvus:
            print("INFO: Using FAISS fallback for tag matching (Milvus unavailable)")

        relevant_docs_names = tag_vector_db.similarity_search_with_score(tag_ans.content)
        tags = [tup for tup in relevant_docs_names if tup[1] <= 0.30]
        print(tags)
        return tags

    def fetch_similar_docs(self, user_query: str):
        configs = read_config_json(self.client_name, self.project_name)
        llm_chain_parameters = LlmChainParameters(**configs)
        tags = self.fetch_tags_from_query(user_query)
        similar_docs = []

        for tag in tags:
            filenames = tag[0].metadata['document'].split('.')
            if llm_chain_parameters.doc_type == filenames[1]:
                file_type = filenames[1]
            else:
                file_type = llm_chain_parameters.doc_type
            document_path = get_llm_document_path(self.client_name, self.project_name, filenames[0], file_type)
            document_data = self.document_loader.load_document([document_path], llm_chain_parameters=llm_chain_parameters)
            if not document_data:
                continue
            else:
                faiss_db = self.get_faiss_db(document_data, filenames)
                similarity_search = faiss_db.similarity_search_with_score(user_query, k=3)
                filtered_docs = [tup for tup in similarity_search if tup[1] <= 0.30]

                for doc in filtered_docs:
                    similar_docs.append(doc[0].page_content)

        return similar_docs

    def get_faiss_db(self, document_data, filenames):
        vectorstore_locations = self.faiss_vectorstore.local_vectorstore_location(self.client_name)
        index_name = self.faiss_vectorstore.client_index(self.client_name, self.project_name)

        if len(filenames) !=0:
            index_name = f"{index_name}_{filenames[0]}"

        if not os.path.exists(vectorstore_locations):
            os.makedirs(vectorstore_locations)

        vector_store = os.listdir(vectorstore_locations)
        matching_files = [filename for filename in vector_store if filename.startswith(index_name)]

        if len(matching_files) == 0:
            faiss_db = self.faiss_vectorstore.load_vectorstore(document_data)
            self.faiss_vectorstore.save_db_local(faiss_db, self.client_name, self.project_name, index_name)
        else:
            faiss_db = self.faiss_vectorstore.load_local_vectorstore(self.client_name, self.project_name, index_name)

        return faiss_db
