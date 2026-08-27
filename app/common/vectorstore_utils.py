import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings


def create_load_vector_store(client_name, project_name, data):
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
    vectorstore_locations = os.path.join(
        os.getcwd(),
        'app',
        'vector_stores',
        client_name
    )
    index_name = f"{client_name}_{project_name}"

    if not os.path.exists(vectorstore_locations):
        os.makedirs(vectorstore_locations)

    vector_store = os.listdir(vectorstore_locations)
    matching_files = [filename for filename in vector_store if filename.startswith(index_name)]
    if len(matching_files) == 0:
        print("Creating the vector store locally")
        db = FAISS.from_documents(data, embeddings)
        db.save_local(folder_path=vectorstore_locations, index_name=index_name)
    else:
        print("Loading the vector store")
        db = FAISS.load_local(folder_path=vectorstore_locations, index_name=index_name, embeddings=embeddings)
    return db
