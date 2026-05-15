import sqlite3
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

def load_documents_from_db():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT url, title, content FROM documents")
    rows = cursor.fetchall()
    conn.close()

    docs = []
    for url, title, content in rows:
        docs.append({
            "url": url,
            "title": title,
            "content": content
        })
    print(f"Loaded {len(docs)} documents from DB")
    return docs

def chunk_documents(docs: list[dict]):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " "]
    )

    all_chunks = []
    for doc in docs:
        chunks = splitter.split_text(doc["content"])
        for chunk in chunks:
            all_chunks.append({
                "text": chunk,
                "metadata": {
                    "url": doc["url"],
                    "title": doc["title"]
                }
            })

    print(f"Total chunks created: {len(all_chunks)}")
    return all_chunks

def build_faiss_index(chunks: list[dict]):
    print("Loading embedding model...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    texts = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    print("Building FAISS index — this will take 2-3 minutes...")
    vectorstore = FAISS.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas
    )

    vectorstore.save_local("faiss_index")
    print("FAISS index saved to faiss_index/")
    return vectorstore

if __name__ == "__main__":
    docs = load_documents_from_db()
    chunks = chunk_documents(docs)
    build_faiss_index(chunks)