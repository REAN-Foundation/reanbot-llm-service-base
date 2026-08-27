from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import CSVLoader
from langchain_community.document_loaders import PyPDFLoader,JSONLoader
from app.domain_types.schemas.llm_service import LlmChainParameters
from itertools import chain

class DocumentLoader:

    def load_document(self, list_of_doc_path,**kwargs):
        try:
            llm_chain_parameters:LlmChainParameters = kwargs.get("llm_chain_parameters",{})
            if llm_chain_parameters.doc_type == "txt":
                document_data = self.text_document_loader(list_of_doc_path, **kwargs)
                return document_data
            elif llm_chain_parameters.doc_type == "csv":
                document_data = self.csv_document_loader(list_of_doc_path, **kwargs)
                return document_data
            elif llm_chain_parameters.doc_type == "pdf":
                document_data = self.pdf_document_loader(list_of_doc_path, **kwargs)
                return document_data
            elif llm_chain_parameters.doc_type == "json":
                document_data = self.json_document_loader(list_of_doc_path, **kwargs)
                return document_data
        except Exception as e:
            print(e)

    def text_document_loader(self, list_of_doc_path,**kwargs):
        llm_chain_parameters:LlmChainParameters = kwargs.get("llm_chain_parameters",{})
        final_text = ""
        for ele in list_of_doc_path:
            try:
                with open(ele, 'r', encoding='utf-8') as f:
                    text = f.read()
                    final_text += text + '\n'
            except IOError:
                continue
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=llm_chain_parameters.chunk_size,
            chunk_overlap=llm_chain_parameters.chunk_overlap
        )
        chunks = text_splitter.create_documents([final_text])
        return chunks

    def csv_document_loader(self, list_of_doc_path, **kwargs):
        metadata_columns = kwargs.get("metadata_columns", None)
        source_column = kwargs.get("source_column", None)
        try:
            final_data = []
            for ele in list_of_doc_path:
                loader = CSVLoader(ele, source_column=source_column, metadata_columns=metadata_columns) if metadata_columns and source_column else CSVLoader(ele, autodetect_encoding=True)
                data = loader.load()
                final_data.append(data)

            return list(chain.from_iterable(final_data))
        
        except Exception as e:
            print(e)

    def json_document_loader(self, list_of_doc_path, **kwargs):
        metadata_columns = kwargs.get("metadata_columns", None)
        source_column = kwargs.get("source_column", None)
        try:
            final_data = []
            for ele in list_of_doc_path:
                if metadata_columns and source_column:
                    loader = JSONLoader(
                        file_path=ele,
                        jq_schema=".[]",
                        content_key= source_column,
                        metadata_func=self.metadata_func
                    )
                else:
                    loader = JSONLoader(
                        file_path=ele,
                        jq_schema=".[]",
                        text_content=False
                    )
                data = loader.load()
                final_data.append(data)
            return list(chain.from_iterable(final_data))

        except Exception as e:
            print(e)


    def pdf_document_loader(self, list_of_doc_path, **kwargs):
        # llm_chain_parameters:LlmChainParameters = kwargs.get("llm_chain_parameters", {})
        pages = []
        for doc_path in list_of_doc_path:
            loader = PyPDFLoader(doc_path)
            intermediate_step = loader.load_and_split()
            pages.append(intermediate_step)
        final_pages = []
        for sub_lists in pages:
            final_pages.extend(sub_lists)

        return final_pages


    def metadata_func(self, record: dict, metadata:dict, metadata_columns:[]) -> dict:
        for column in metadata_columns:
            metadata[column] = record.get(column)

        return metadata
