# import os
# from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_community.vectorstores import Chroma

# # Set your custom cache directory
# os.environ["HF_HOME"] = "D:/huggingface_cache"

# def build_vector_db():
#     # 1. Initialize your specific embedding model
#     embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
#     # 2. Load all PDFs from your knowledge folder
#     # Ensure you have a folder named 'data/knowledge' with your PDFs in it
#     if not os.path.exists("data/GI_Diabetes"):
#         os.makedirs("data/knowledge")
#         print("Please put your medical PDFs in 'data/knowledge' and run again.")
#         return

#     loader = DirectoryLoader("data/GI_Diabetes", glob="./*.pdf", loader_cls=PyPDFLoader)
#     documents = loader.load()
    
#     # 3. Split text into chunks for better retrieval
#     text_splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=70)
#     texts = text_splitter.split_documents(documents)
    
#     # 4. Create and persist the Vector Database
#     vector_db = Chroma.from_documents(
#         documents=texts,
#         embedding=embeddings,
#         persist_directory="./chroma_db"
#     )
#     print(f"✅ Indexed {len(texts)} chunks into ./chroma_db")

# if __name__ == "__main__":
#     build_vector_db()




import os
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Set your custom cache directory (for local model storage)
os.environ["HF_HOME"] = "D:/huggingface_cache"

DATA_PATH = "data"          # Folder where your PDFs are
DB_PATH = "./chroma_db"     # Where vector DB will be stored

def build_vector_db():

    # 1️⃣ Initialize embedding model (runs locally after first download)
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"local_files_only": False}  # change to True after first download if you want strict offline
    )

    # 2️⃣ Check if data folder exists
    if not os.path.exists(DATA_PATH):
        print(f"❌ Folder '{DATA_PATH}' does not exist.")
        return

    # 3️⃣ Load all PDFs inside data/
    loader = DirectoryLoader(
        DATA_PATH,
        glob="*.pdf",
        loader_cls=PyPDFLoader
    )

    documents = loader.load()

    if not documents:
        print(f"❌ No PDF files found inside '{DATA_PATH}'.")
        return

    # 4️⃣ Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=70
    )

    texts = text_splitter.split_documents(documents)

    # 5️⃣ Create and persist Chroma vector database
    vector_db = Chroma.from_documents(
        documents=texts,
        embedding=embeddings,
        persist_directory=DB_PATH
    )

    vector_db.persist()

    print(f"✅ Indexed {len(texts)} chunks into '{DB_PATH}'")

if __name__ == "__main__":
    build_vector_db()