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


def build_rag_chain(api_key=None, model_name=None):
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    vectorstore = FAISS.load_local(
        FAISS_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )


    groq_key = api_key or os.getenv("GROQ_API_KEY")
    if not groq_key:
        llm = None
    else:
        target_model = model_name or os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
        llm = ChatGroq(
            model=target_model,
            api_key=groq_key,
            temperature=0.2
        )


    prompt = ChatPromptTemplate.from_template(
        "You are a professional research assistant. Answer the question accurately using ONLY the context provided below.\n"
        "Be concise, clear, and structured.\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n\n"
        "Answer:"
    )

    return llm, prompt, vectorstore


def ask(query, api_key=None, history_context="", model_name=None):
    docs = load_chunks_from_db()
    llm, prompt, vectorstore = build_rag_chain(api_key=api_key, model_name=model_name)


    # For follow-ups, resolve query context if history_context is provided
    search_query = query
    if history_context and len(history_context.strip()) > 0:
        search_query = f"{history_context} {query}"

    results = hybrid_search(search_query, docs, vectorstore, k=5)

    context = "\n\n".join([d.page_content for d in results])
    
    # Detailed sources list
    rich_sources = []
    seen_titles = set()
    for d in results:
        t = d.metadata.get("title", "Document")
        if t not in seen_titles:
            seen_titles.add(t)
            rich_sources.append({
                "title": t,
                "url": d.metadata.get("url", ""),
                "snippet": d.page_content[:250] + ("..." if len(d.page_content) > 250 else "")
            })

    simple_sources = list(seen_titles)

    if not llm:
        answer_text = (
            "No Groq API Key was detected. Please provide your GROQ_API_KEY in the Settings view "
            "or set it as an environment variable to enable live LLM response synthesis.\n\n"
            "Below are the relevant documents retrieved from the hybrid index for your query:"
        )
    else:
        full_question = query
        if history_context:
            full_question = f"[Prior Context: {history_context}]\nQuestion: {query}"
        
        chain = prompt | llm
        try:
            response = chain.invoke({
                "context": context,
                "question": full_question
            })
            answer_text = response.content
        except Exception as e:
            err_msg = str(e)
            if "404" in err_msg or "model_not_found" in err_msg:
                answer_text = f"Groq API Error: Model unavailable or not found. Please check model configuration.\n\nRetrieved context was extracted successfully."
            elif "401" in err_msg or "authentication" in err_msg.lower():
                answer_text = "Groq API Error: Authentication failed (401). Check GROQ_API_KEY in settings or environment.\n\nRetrieved context was extracted successfully."
            else:
                answer_text = f"LLM Generation Error: {err_msg}\n\nRetrieved context was extracted successfully."

    return {
        "answer": answer_text,
        "sources": simple_sources,
        "rich_sources": rich_sources,
        "raw_docs": [d.page_content for d in results]
    }


if __name__ == "__main__":
    result = ask("What is retrieval augmented generation?")
    print("\nAnswer:")
    print(result["answer"])
    print("\nSources:")
    for s in result["sources"]:
        print(f"  - {s}")