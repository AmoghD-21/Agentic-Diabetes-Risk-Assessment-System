import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

os.environ["HF_HOME"] = "D:/huggingface_cache"

def get_retriever():
    # Must use the exact same embedding model used during ingestion
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    if not os.path.exists("./chroma_db"):
        return None
        
    vector_db = Chroma(
        persist_directory="./chroma_db",
        embedding_function=embeddings
    )
    # k=3 retrieves the top 3 most relevant medical facts
    return vector_db.as_retriever(search_kwargs={"k": 3})