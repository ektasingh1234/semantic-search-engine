import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import time
from app.rag.rag_chain import load_chunks_from_db, build_rag_chain, hybrid_search
from app.pdf_handler import process_pdf, ask_pdf
from app.auth import register_user, login_user, init_users_db

st.set_page_config(
    page_title="NeuroSearch",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_users_db()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif; }
.stApp { background: #07070f; }

[data-testid="stSidebar"] {
    background: #0f0f1a !important;
    border-right: 1px solid #1a1a2e !important;
}
[data-testid="stSidebar"] * { color: #9ca3af !important; }
.sidebar-title { font-size: 1.1rem; font-weight: 700; color: #a78bfa !important; margin-bottom: 1rem; }
.sidebar-stat { background: #1a1a2e; border-radius: 10px; padding: 0.6rem 0.9rem; margin-bottom: 8px; font-size: 0.8rem; }
.sidebar-stat span { color: #a78bfa !important; font-weight: 600; }

/* Auth page */
.auth-container {
    max-width: 420px; margin: 5rem auto; padding: 2.5rem;
    background: #0f0f1a; border: 1px solid #1a1a2e;
    border-radius: 20px;
}
.auth-title {
    font-size: 2rem; font-weight: 800; text-align: center;
    background: linear-gradient(135deg, #818cf8, #a78bfa, #c084fc);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0.25rem;
}
.auth-sub { text-align: center; color: #4b5563; font-size: 0.88rem; margin-bottom: 2rem; }

.stTextInput > div > div > input {
    background: #0f0f1a !important; border: 1.5px solid #1e1e35 !important;
    border-radius: 12px !important; color: #e5e7eb !important;
    font-size: 0.95rem !important; padding: 0.8rem 1rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.12) !important;
}
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important; border: none !important;
    border-radius: 12px !important; font-weight: 600 !important;
    font-size: 0.95rem !important; width: 100% !important;
    padding: 0.8rem !important; margin-top: 0.5rem !important;
}

.chat-container { max-width: 820px; margin: 0 auto; padding: 1rem 1rem 140px 1rem; }
.msg-user { display: flex; justify-content: flex-end; margin: 1rem 0; animation: fadein 0.3s ease; }
.msg-user .bubble {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white; padding: 0.85rem 1.2rem;
    border-radius: 18px 18px 4px 18px;
    max-width: 70%; font-size: 0.95rem; line-height: 1.6;
}
.msg-ai { display: flex; justify-content: flex-start; gap: 10px; margin: 1rem 0; animation: fadein 0.3s ease; }
.ai-avatar {
    width: 32px; height: 32px; border-radius: 50%; flex-shrink: 0;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    display: flex; align-items: center; justify-content: center;
    font-size: 14px; margin-top: 2px;
}
.msg-ai .bubble {
    background: #0f0f1a; border: 1px solid #1a1a2e;
    color: #d1d5db; padding: 0.85rem 1.2rem;
    border-radius: 4px 18px 18px 18px;
    max-width: 75%; font-size: 0.95rem; line-height: 1.8;
}
.source-chip {
    display: inline-flex; align-items: center; gap: 4px;
    background: #1a1a2e; border: 1px solid #2a2a45;
    color: #a78bfa; padding: 3px 10px; border-radius: 20px;
    font-size: 0.72rem; font-weight: 500; margin: 3px 3px 0 0;
}
.timing { font-size: 0.7rem; color: #374151; margin-top: 6px; }
@keyframes fadein { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }
.welcome { text-align: center; padding: 4rem 2rem 2rem 2rem; }
.welcome h1 {
    font-size: 3rem; font-weight: 800;
    background: linear-gradient(135deg, #818cf8, #a78bfa, #c084fc);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
}
.welcome p { color: #374151; font-size: 0.95rem; margin-bottom: 2rem; }
.suggest-label { text-align: center; font-size: 0.7rem; color: #374151; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 1rem; }
div[data-testid="stSpinner"] p { color: #6366f1 !important; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource(show_spinner=False)
def get_components():
    docs = load_chunks_from_db()
    llm, prompt, vectorstore = build_rag_chain()
    return docs, llm, prompt, vectorstore

# Session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = ""
if "pdf_vectorstore" not in st.session_state:
    st.session_state.pdf_vectorstore = None
if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = None
if "mode" not in st.session_state:
    st.session_state.mode = "wiki"
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"

SUGGESTIONS = [
    "What is Retrieval-Augmented Generation?",
    "How do transformers work?",
    "What is a vector database?",
    "Explain deep learning",
]

# AUTH PAGE
if not st.session_state.logged_in:
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown("""
        <div class="auth-title">⚡ NeuroSearch</div>
        <div class="auth-sub">Hybrid RAG Search · Powered by LangChain & Groq</div>
        """, unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["Login", "Sign Up"])

        with tab1:
            st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)
            login_username = st.text_input("Username", placeholder="Enter username", key="login_user")
            login_password = st.text_input("Password", placeholder="Enter password", type="password", key="login_pass")
            if st.button("Login →", key="login_btn"):
                if login_username and login_password:
                    result = login_user(login_username, login_password)
                    if result["success"]:
                        st.session_state.logged_in = True
                        st.session_state.username = result["username"]
                        st.rerun()
                    else:
                        st.error(result["message"])
                else:
                    st.warning("Please fill all fields.")

        with tab2:
            st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)
            reg_username = st.text_input("Username", placeholder="Choose a username", key="reg_user")
            reg_email = st.text_input("Email", placeholder="Enter your email", key="reg_email")
            reg_password = st.text_input("Password", placeholder="Choose a password", type="password", key="reg_pass")
            reg_confirm = st.text_input("Confirm Password", placeholder="Confirm password", type="password", key="reg_confirm")
            if st.button("Create Account →", key="reg_btn"):
                if reg_username and reg_email and reg_password and reg_confirm:
                    if reg_password != reg_confirm:
                        st.error("Passwords do not match.")
                    elif len(reg_password) < 6:
                        st.error("Password must be at least 6 characters.")
                    else:
                        result = register_user(reg_username, reg_email, reg_password)
                        if result["success"]:
                            st.success("Account created! Please login.")
                        else:
                            st.error(result["message"])
                else:
                    st.warning("Please fill all fields.")
    st.stop()

# MAIN APP — only reached if logged in
with st.sidebar:
    st.markdown('<div class="sidebar-title">⚡ NeuroSearch</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sidebar-stat">User &nbsp;<span>{st.session_state.username}</span></div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🌐 Wiki", key="mode_wiki"):
            st.session_state.mode = "wiki"
            st.session_state.messages = []
            st.rerun()
    with col_b:
        if st.button("📄 PDF", key="mode_pdf"):
            st.session_state.mode = "pdf"
            st.session_state.messages = []
            st.rerun()

    st.markdown(f'<p style="font-size:0.75rem; color:#6366f1; margin-bottom:1rem;">Active: {"🌐 Wiki Search" if st.session_state.mode == "wiki" else "📄 PDF Chat"}</p>', unsafe_allow_html=True)

    if st.session_state.mode == "wiki":
        st.markdown("""
        <div class="sidebar-stat">Model &nbsp;<span>Groq LLaMA3</span></div>
        <div class="sidebar-stat">Retrieval &nbsp;<span>BM25 + FAISS</span></div>
        <div class="sidebar-stat">Docs &nbsp;<span>10 Wikipedia</span></div>
        """, unsafe_allow_html=True)
    else:
        uploaded_file = st.file_uploader("", type=["pdf"], label_visibility="collapsed")
        if uploaded_file:
            if st.session_state.pdf_name != uploaded_file.name:
                with st.spinner("Processing PDF..."):
                    st.session_state.pdf_vectorstore = process_pdf(uploaded_file)
                    st.session_state.pdf_name = uploaded_file.name
                    st.session_state.messages = []
                st.success("✅ Ready!")

    st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)
    if st.button("🗑️ Clear chat", key="clear"):
        st.session_state.messages = []
        st.rerun()

    if st.button("🚪 Logout", key="logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    if st.session_state.messages:
        st.markdown('<p style="font-size:0.7rem; color:#374151; text-transform:uppercase; letter-spacing:1px; margin-top:1.2rem; margin-bottom:0.5rem;">History</p>', unsafe_allow_html=True)
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                q = msg["content"][:38] + "..." if len(msg["content"]) > 38 else msg["content"]
                st.markdown(f'<div style="background:#13131f;border:1px solid #1e1e35;border-radius:8px;padding:0.45rem 0.75rem;margin-bottom:5px;font-size:0.75rem;color:#6b7280;">🔍 {q}</div>', unsafe_allow_html=True)

# Chat area
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

if not st.session_state.messages:
    if st.session_state.mode == "wiki":
        st.markdown(f"""
        <div class="welcome">
            <h1>⚡ NeuroSearch</h1>
            <p>Welcome back, {st.session_state.username}! Ask anything about ML, AI, LLMs.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="suggest-label">Try asking</div>', unsafe_allow_html=True)
        _, c1, c2, c3, c4, _ = st.columns([0.3, 1.8, 1.8, 1.8, 1.8, 0.3])
        clicked = None
        with c1:
            if st.button(SUGGESTIONS[0], key="s0"): clicked = SUGGESTIONS[0]
        with c2:
            if st.button(SUGGESTIONS[1], key="s1"): clicked = SUGGESTIONS[1]
        with c3:
            if st.button(SUGGESTIONS[2], key="s2"): clicked = SUGGESTIONS[2]
        with c4:
            if st.button(SUGGESTIONS[3], key="s3"): clicked = SUGGESTIONS[3]
        if clicked:
            st.session_state.pending_query = clicked
            st.rerun()
    else:
        st.markdown("""
        <div class="welcome">
            <h1>📄 PDF Chat</h1>
            <p>Upload a PDF from the sidebar and ask anything about it</p>
        </div>
        """, unsafe_allow_html=True)
else:
    if st.session_state.mode == "pdf" and st.session_state.pdf_name:
        st.markdown(f'<div style="background:#0f0f1a;border:1px solid #2a2a45;border-radius:12px;padding:0.75rem 1rem;margin-bottom:1rem;"><span style="color:#a78bfa;font-size:0.88rem;">📄 {st.session_state.pdf_name}</span></div>', unsafe_allow_html=True)

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="msg-user"><div class="bubble">{msg["content"]}</div></div>', unsafe_allow_html=True)
        else:
            chips = "".join([f'<span class="source-chip">📄 {s}</span>' for s in msg.get("sources", [])])
            answer_html = msg["content"].replace("\n", "<br>")
            st.markdown(f"""
            <div class="msg-ai">
                <div class="ai-avatar">⚡</div>
                <div>
                    <div class="bubble">{answer_html}</div>
                    <div style="margin-top:8px;">{chips}</div>
                    <div class="timing">⏱ {msg.get("time", "")}s · {"PDF RAG" if st.session_state.mode == "pdf" else "Hybrid RAG"}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Input bar
_, mid, _ = st.columns([0.5, 9, 0.5])
with mid:
    col1, col2 = st.columns([6, 1])
    with col1:
        placeholder = "Ask about your PDF..." if st.session_state.mode == "pdf" else "Ask anything about ML, AI, LLMs..."
        user_input = st.text_input("", placeholder=placeholder, label_visibility="collapsed", key="chat_input")
    with col2:
        send = st.button("Send ➤", key="send_btn")

active_query = st.session_state.pending_query or (user_input if send else "")

if active_query:
    st.session_state.pending_query = ""
    if st.session_state.mode == "pdf" and not st.session_state.pdf_vectorstore:
        st.warning("Please upload a PDF first.")
    else:
        st.session_state.messages.append({"role": "user", "content": active_query})
        with st.spinner("Thinking..."):
            t0 = time.time()
            _, llm, prompt, _ = get_components()
            if st.session_state.mode == "pdf":
                result = ask_pdf(active_query, st.session_state.pdf_vectorstore, llm, prompt)
                answer = result["answer"]
                sources = result["sources"]
            else:
                docs, llm, prompt, vectorstore = get_components()
                results = hybrid_search(active_query, docs, vectorstore, k=5)
                context = "\n\n".join([d.page_content for d in results])
                sources = list(set([d.metadata["title"] for d in results]))
                chain = prompt | llm
                response = chain.invoke({"context": context, "question": active_query})
                answer = response.content
            elapsed = round(time.time() - t0, 2)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources,
            "time": elapsed
        })
        st.rerun()