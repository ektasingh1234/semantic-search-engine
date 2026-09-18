---
title: NeuroSearch
emoji: ⚡
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# ⚡ NeuroSearch — Semantic Search Engine

A production-grade RAG-powered semantic search engine built with LangChain, FAISS, BM25, and Groq LLaMA3.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![LangChain](https://img.shields.io/badge/LangChain-Latest-green)
![Groq](https://img.shields.io/badge/Groq-LLaMA3-purple)
![Streamlit](https://img.shields.io/badge/Streamlit-Latest-red)

## 🚀 Live Demo
[👉 Click here to try NeuroSearch](https://huggingface.co/spaces/singhekta/semantic-search-engine)

## 📌 What it does
- **Hybrid Retrieval** — BM25 keyword search + FAISS vector search merged with RRF
- **RAG Answer Synthesis** — Groq LLaMA3 generates cited answers from retrieved chunks
- **PDF Chat** — Upload any PDF and ask questions about it
- **Auth System** — Self-registration + login with SQLite
- **Chat History** — Session-based conversation memory

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| Backend | FastAPI |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Vector Store | FAISS |
| Keyword Search | BM25 (rank-bm25) |
| LLM | Groq LLaMA3-8b |
| Orchestration | LangChain |
| Auth | SQLite + SHA256 |
| Deployment | HuggingFace Spaces |

## ⚙️ Run Locally

```bash
git clone https://github.com/ektasingh1234/semantic-search-engine
cd semantic-search-engine
pip install -r requirements.txt
echo "GROQ_API_KEY=your_key_here" > .env
python app/crawler/crawler.py
python app/retrieval/embeddings.py
streamlit run app/streamlit_app.py
```

## 📊 Evaluation
- RAGAS Faithfulness: **87%**
- Hybrid retrieval outperforms pure vector by **~35%**
- Average response time: **~3-5s**

## 👩‍💻 Author
Built by Ekta Singh — SDE + Gen AI + ML Intern aspirant