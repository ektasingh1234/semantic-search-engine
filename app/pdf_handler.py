import os
import tempfile
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

def process_pdf(uploaded_file) -> FAISS:
    # Save uploaded file to temp safely
    try:
        uploaded_file.seek(0)
    except Exception:
        pass
        
    file_bytes = uploaded_file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    # Load PDF
    loader = PyPDFLoader(tmp_path)
    pages = loader.load()
    try:
        os.unlink(tmp_path)
    except Exception:
        pass

    # Chunk
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(pages)
    if not chunks:
        chunks = [Document(page_content="No text content extracted from PDF.", metadata={"page": 0})]
        
    print(f"PDF chunks created: {len(chunks)}")

    # Embed
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    vectorstore = FAISS.from_documents(chunks, embeddings)
    return vectorstore

def ask_pdf(query: str, vectorstore: FAISS, llm=None, prompt=None) -> dict:
    results = vectorstore.similarity_search(query, k=5)
    context = "\n\n".join([d.page_content for d in results])
    sources = list(set([
        f"Page {d.metadata.get('page', 0) + 1}"
        for d in results
    ]))

    if not llm or not prompt:
        answer_text = (
            "No Groq API Key was detected. Below are the relevant passages extracted from your PDF document:\n\n"
            + context
        )
    else:
        chain = prompt | llm
        try:
            response = chain.invoke({
                "context": context,
                "question": query
            })
            answer_text = response.content
        except Exception as e:
            answer_text = f"LLM Generation Error: {str(e)}\n\nExtracted PDF Passages:\n{context}"

    return {
        "answer": answer_text,
        "sources": sources
    }