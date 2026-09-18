import os
import sqlite3
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DB_PATH = os.path.join(PROJECT_ROOT, "data.db")
FAISS_PATH = os.path.join(PROJECT_ROOT, "faiss_index")

def load_chunks_from_db():
    conn = sqlite3.connect(DATA_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT url, title, content FROM documents")
    rows = cursor.fetchall()
    conn.close()


    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " "]
    )

    all_docs = []
    for url, title, content in rows:
        chunks = splitter.split_text(content)
        for chunk in chunks:
            all_docs.append(Document(
                page_content=chunk,
                metadata={"url": url, "title": title}
            ))

    print(f"Total chunks loaded: {len(all_docs)}")
    return all_docs

def hybrid_search(query: str, docs, vectorstore, k=5):
    # FAISS vector search
    faiss_results = vectorstore.similarity_search(query, k=k)

    # BM25 keyword search
    bm25 = BM25Retriever.from_documents(docs)
    bm25.k = k
    bm25_results = bm25.invoke(query)

    # Merge results — RRF (Reciprocal Rank Fusion)
    seen = set()
    merged = []
    for doc in faiss_results + bm25_results:
        key = doc.page_content[:100]
        if key not in seen:
            seen.add(key)
            merged.append(doc)

    return merged[:k]

def build_vectorstore():
    print("Loading FAISS index...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    vectorstore = FAISS.load_local(
        FAISS_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )
    return vectorstore


if __name__ == "__main__":
    docs = load_chunks_from_db()
    vectorstore = build_vectorstore()

    query = "What is retrieval augmented generation?"
    print(f"\nQuery: {query}")
    results = hybrid_search(query, docs, vectorstore, k=5)

    print(f"\nTop {len(results)} results:")
    for i, doc in enumerate(results):
        print(f"\n--- Result {i+1} ---")
        print(f"Source: {doc.metadata['title']}")
        print(f"Content: {doc.page_content[:200]}...")