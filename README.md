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

![Python](https://img.shields.io/badge/Python-3.11-blue)
![LangChain](https://img.shields.io/badge/LangChain-v1.3-green)
![Groq](https://img.shields.io/badge/Groq-Qwen%203.8%2027B-orange)
![Streamlit](https://img.shields.io/badge/Streamlit-v1.57-red)
[![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/singhekta/semantic-search-engine)

## 🚀 Live Demo

🤗 **Hugging Face Space**: [https://huggingface.co/spaces/singhekta/semantic-search-engine](https://huggingface.co/spaces/singhekta/semantic-search-engine)  
⚡ **Direct Web App**: [https://singhekta-semantic-search-engine.hf.space](https://singhekta-semantic-search-engine.hf.space)

## 📌 What it does
- **Hybrid Retrieval** — BM25 keyword search + FAISS vector search merged with RRF
- **RAG Answer Synthesis** — Groq High-Speed API (Qwen 3.8 27B) generates cited answers from retrieved chunks
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
| LLM | Groq Qwen 3.8 27B |
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