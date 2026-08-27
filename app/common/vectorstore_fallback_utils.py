import os
import logging
from typing import Tuple, Any

logger = logging.getLogger(__name__)


def has_milvus_credentials() -> bool:
    """
    Check if MILVUS_URI and MILVUS_TOKEN environment variables exist and are non-empty.

    Returns:
        bool: True if both credentials are present and non-empty, False otherwise
    """
    milvus_uri = os.environ.get("MILVUS_URI")
    milvus_token = os.environ.get("MILVUS_TOKEN")

    if not milvus_uri or not milvus_token:
        return False

    if milvus_uri.strip() == "" or milvus_token.strip() == "":
        return False

    return True


def create_tag_vectorstore_with_fallback(
    milvus_store,
    faiss_store,
    documents,
    client_name="tags",
    project_name="keywords"
) -> Tuple[Any, bool]:
    """
    Attempt to create a Milvus vectorstore for tags, fallback to FAISS on any error.

    This function implements immediate fallback without retry logic. It tries to create
    a Milvus vectorstore and catches all exceptions (missing credentials, connection
    failures, timeouts, etc.) to fallback to a local FAISS index.

    Args:
        milvus_store: MilvusVectorstore instance
        faiss_store: FaissVectorstore instance
        documents: List of Document objects to store
        client_name: Client identifier (default: "tags")
        project_name: Project identifier (default: "keywords")

    Returns:
        Tuple[VectorStore, bool]: (vectorstore instance, is_milvus flag)
            - vectorstore: Either Milvus or FAISS vectorstore instance
            - is_milvus: True if using Milvus, False if using FAISS fallback
    """
    # First check if credentials are present
    if not has_milvus_credentials():
        logger.warning("Milvus credentials missing (MILVUS_URI or MILVUS_TOKEN not set), using FAISS for tag matching")
        faiss_db = get_or_create_tag_faiss_index(faiss_store, documents, client_name, project_name)
        return faiss_db, False

    # Try to connect to Milvus
    try:
        logger.info("Attempting to connect to Milvus for tag vectorstore")
        tag_vector_db = milvus_store.load_vectorstore(
            documents,
            client_name=client_name,
            project_name=project_name
        )
        logger.info("Successfully connected to Milvus for tag matching")
        return tag_vector_db, True

    except ImportError as e:
        # Handle missing pymilvus.exceptions module gracefully
        logger.error(f"Milvus library import error: {e}, falling back to FAISS")
        faiss_db = get_or_create_tag_faiss_index(faiss_store, documents, client_name, project_name)
        return faiss_db, False

    except Exception as e:
        # Catch all exceptions: ConnectionError, TimeoutError, MilvusException, ValueError, etc.
        error_type = type(e).__name__
        logger.warning(f"Milvus connection failed ({error_type}: {e}), falling back to FAISS")
        faiss_db = get_or_create_tag_faiss_index(faiss_store, documents, client_name, project_name)
        return faiss_db, False


def get_or_create_tag_faiss_index(
    faiss_store,
    documents,
    client_name="tags",
    project_name="keywords"
) -> Any:
    """
    Load existing FAISS index for tags or create a new one if it doesn't exist.

    The FAISS index is stored at: app/vector_stores/tags/tags_keywords.faiss

    Args:
        faiss_store: FaissVectorstore instance
        documents: List of Document objects to store (used if creating new index)
        client_name: Client identifier (default: "tags")
        project_name: Project identifier (default: "keywords")

    Returns:
        FAISS vectorstore instance
    """
    try:
        # Attempt to load existing FAISS index
        vectorstore_location = faiss_store.local_vectorstore_location(client_name)
        index_name = faiss_store.client_index(client_name, project_name)

        # Check if the directory exists
        if os.path.exists(vectorstore_location):
            vector_store_files = os.listdir(vectorstore_location)
            matching_files = [f for f in vector_store_files if f.startswith(index_name)]

            if len(matching_files) > 0:
                logger.info(f"Loading existing FAISS index for tags from {vectorstore_location}/{index_name}")
                faiss_db = faiss_store.load_local_vectorstore(client_name, project_name)
                return faiss_db

        # If index doesn't exist, create it
        logger.info(f"Creating new FAISS index for tags at {vectorstore_location}/{index_name}")
        faiss_db = faiss_store.load_vectorstore(documents)

        # Save the index for future use
        faiss_store.save_db_local(faiss_db, client_name, project_name)
        logger.info(f"FAISS index created and saved at {vectorstore_location}/{index_name}")

        return faiss_db

    except Exception as e:
        logger.error(f"Failed to create/load FAISS index for tags: {e}")
        # As a last resort, create in-memory FAISS index without persistence
        logger.warning("Creating non-persistent in-memory FAISS index as fallback")
        faiss_db = faiss_store.load_vectorstore(documents)
        return faiss_db
