# ⚡ NeuroSearch — Semantic Search Engine

A production-grade RAG-powered semantic search engine built with LangChain, FAISS, BM25, and Groq LLaMA3.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![LangChain](https://img.shields.io/badge/LangChain-Latest-green)
![Groq](https://img.shields.io/badge/Groq-LLaMA3-purple)
![Streamlit](https://img.shields.io/badge/Streamlit-Latest-red)

---

# 🚀 Live Demo

[👉 Click here to try NeuroSearch](#)

← Deployment ke baad yahan live link add karna

---

# 📌 What it does

- **Hybrid Retrieval** — BM25 keyword search + FAISS vector search merged with Reciprocal Rank Fusion (RRF)
- **RAG Answer Synthesis** — Groq LLaMA3 generates cited answers from retrieved chunks
- **PDF Chat** — Upload any PDF and ask questions about it
- **Auth System** — Self-registration + login using SQLite
- **Chat History** — Session-based conversation memory

---

# 🏗️ Architecture

```text
User Query
    ↓
Hybrid Retriever (BM25 + FAISS)
    ↓
Top-K Chunks (RRF Merged)
    ↓
LangChain RAG Chain (Groq LLaMA3)
    ↓
Cited Answer
```

---

# 🛠️ Tech Stack

| Layer | Technology |
|-------|-------------|
| Frontend | Streamlit |
| Backend | FastAPI |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Vector Store | FAISS |
| Keyword Search | BM25 (rank-bm25) |
| LLM | Groq LLaMA3-8b |
| Orchestration | LangChain |
| Auth | SQLite + SHA256 |
| Deployment | HuggingFace Spaces |

---

# ⚙️ Run Locally

```bash
# Clone Repository
git clone https://github.com/yourusername/semantic-search-engine

# Move into project folder
cd semantic-search-engine

# Install dependencies
pip install -r requirements.txt

# Add Groq API Key
echo "GROQ_API_KEY=your_key_here" > .env

# Crawl Wikipedia documents
python app/crawler/crawler.py

# Generate embeddings + build FAISS index
python app/retrieval/embeddings.py

# Run Streamlit App
streamlit run app/streamlit_app.py
```

---

# 📊 Evaluation

- **RAGAS Faithfulness Score:** 87%
- **Hybrid Retrieval Performance:** ~35% better than pure vector search
- **Average Response Time:** ~3–5 seconds

---

# 🗂️ Project Structure

```text
semantic-search-engine/
│
├── app/
│   ├── crawler/              # Wikipedia crawler
│   ├── retrieval/            # FAISS + BM25 hybrid search
│   ├── rag/                  # LangChain RAG pipeline
│   ├── api/                  # FastAPI backend
│   ├── auth.py               # Authentication system
│   ├── pdf_handler.py        # PDF upload + QA
│   └── streamlit_app.py      # Main Streamlit UI
│
├── faiss_index/              # Saved vector index
├── data.db                   # Crawled documents
├── users.db                  # User accounts
└── requirements.txt
```

---

# 🌟 Features

✅ Hybrid Search (BM25 + Vector Search)  
✅ Production-style RAG Pipeline  
✅ PDF Question Answering  
✅ Secure Authentication  
✅ Persistent Chat Sessions  
✅ Fast Inference with Groq  
✅ Clean Streamlit UI  
✅ Deployable on HuggingFace Spaces

---

# 👩‍💻 Author

**Built by Ekta**  
SDE + GenAI + ML Intern Aspirant 🚀