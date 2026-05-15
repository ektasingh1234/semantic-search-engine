import os
import sqlite3
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

def load_chunks_from_db():
    conn = sqlite3.connect("data.db")
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
    return all_docs


def hybrid_search(query, docs, vectorstore, k=5):
    faiss_results = vectorstore.similarity_search(query, k=k)

    bm25 = BM25Retriever.from_documents(docs)
    bm25.k = k
    bm25_results = bm25.invoke(query)

    seen = set()
    merged = []
    for doc in faiss_results + bm25_results:
        key = doc.page_content[:100]
        if key not in seen:
            seen.add(key)
            merged.append(doc)

    return merged[:k]


def build_rag_chain():
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    vectorstore = FAISS.load_local(
        "faiss_index",
        embeddings,
        allow_dangerous_deserialization=True
    )

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0
    )

    prompt = ChatPromptTemplate.from_template(
        "You are a helpful assistant. Answer the question using ONLY the context below.\n"
        "At the end, cite the sources used.\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n\n"
        "Answer with citations:"
    )

    return llm, prompt, vectorstore


def ask(query):
    docs = load_chunks_from_db()
    llm, prompt, vectorstore = build_rag_chain()

    results = hybrid_search(query, docs, vectorstore, k=5)

    context = "\n\n".join([d.page_content for d in results])
    sources = list(set([d.metadata["title"] for d in results]))

    chain = prompt | llm
    response = chain.invoke({
        "context": context,
        "question": query
    })

    return {
        "answer": response.content,
        "sources": sources
    }


if __name__ == "__main__":
    result = ask("What is retrieval augmented generation?")
    print("\nAnswer:")
    print(result["answer"])
    print("\nSources:")
    for s in result["sources"]:
        print(f"  - {s}")