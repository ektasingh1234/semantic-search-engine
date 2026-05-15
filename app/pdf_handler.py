import os
import tempfile
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

def process_pdf(uploaded_file) -> FAISS:
    # Save uploaded file to temp
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    # Load PDF
    loader = PyPDFLoader(tmp_path)
    pages = loader.load()
    os.unlink(tmp_path)

    # Chunk
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(pages)
    print(f"PDF chunks created: {len(chunks)}")

    # Embed
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    vectorstore = FAISS.from_documents(chunks, embeddings)
    return vectorstore

def ask_pdf(query: str, vectorstore: FAISS, llm, prompt) -> dict:
    results = vectorstore.similarity_search(query, k=5)
    context = "\n\n".join([d.page_content for d in results])
    sources = list(set([
        f"Page {d.metadata.get('page', '?') + 1}"
        for d in results
    ]))

    chain = prompt | llm
    response = chain.invoke({
        "context": context,
        "question": query
    })

    return {
        "answer": response.content,
        "sources": sources
    }