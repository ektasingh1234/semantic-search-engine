import sys
import os
import sqlite3
import time
import uuid
import streamlit as st
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.rag.rag_chain import load_chunks_from_db, build_rag_chain, hybrid_search
from app.pdf_handler import process_pdf, ask_pdf
from app.auth import (
    register_user, login_user, init_users_db,
    save_history_entry, fetch_user_history, clear_user_history,
    save_research_note, fetch_user_saved_notes, delete_saved_note
)
from app.icons import render_icon
from app.ui_styles import CSS_STYLES

# Page Setup
st.set_page_config(
    page_title="NeuroSearch — Knowledge Engine",
    page_icon="https://raw.githubusercontent.com/feathericons/feather/master/icons/search.svg",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize DBs
init_users_db()

# Apply Clean SaaS CSS
st.markdown(CSS_STYLES, unsafe_allow_html=True)

# Cached Backend Resources
@st.cache_resource(show_spinner=False)
def get_cached_components():
    docs = load_chunks_from_db()
    try:
        llm, prompt, vectorstore = build_rag_chain()
        return docs, llm, prompt, vectorstore, None
    except Exception as err:
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vectorstore = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        return docs, None, None, vectorstore, str(err)

# Session State Initialization
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "active_view" not in st.session_state:
    st.session_state.active_view = "home"
if "search_mode" not in st.session_state:
    st.session_state.search_mode = "wiki"
if "top_k" not in st.session_state:
    st.session_state.top_k = 5
if "history" not in st.session_state:
    st.session_state.history = []
if "saved_results" not in st.session_state:
    st.session_state.saved_results = []
if "pdf_vectorstore" not in st.session_state:
    st.session_state.pdf_vectorstore = None
if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = None
if "pending_query" not in st.session_state:
    st.session_state.pending_query = ""
if "current_search_result" not in st.session_state:
    st.session_state.current_search_result = None
if "target_source_title" not in st.session_state:
    st.session_state.target_source_title = None

# Helper DB query for Documents
def get_all_db_documents():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, url, content FROM documents ORDER BY title ASC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "url": r[2], "content": r[3]} for r in rows]


# Load persistent data for user on login
def load_user_persistent_data(username: str):
    st.session_state.history = fetch_user_history(username)
    st.session_state.saved_results = fetch_user_saved_notes(username)


# ==============================================================================
# AUTHENTICATION PAGE (Login / Register)
# ==============================================================================
if not st.session_state.logged_in:
    st.markdown('<div style="height: 3rem;"></div>', unsafe_allow_html=True)
    _, col_mid, _ = st.columns([1, 2.2, 1])

    with col_mid:
        st.markdown(f"""
        <div class="saas-card" style="padding: 2.5rem; text-align: center;">
            <div style="margin-bottom: 0.75rem;">
                {render_icon("search", 28, "#818cf8")}
            </div>
            <div style="font-size: 1.5rem; font-weight: 700; color: #f8fafc; letter-spacing: -0.02em;">
                NeuroSearch
            </div>
            <div style="font-size: 0.875rem; color: #94a3b8; margin-top: 0.25rem; margin-bottom: 1.5rem;">
                Enterprise Hybrid Knowledge & Research Platform
            </div>
        """, unsafe_allow_html=True)

        tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])

        with tab_login:
            st.markdown('<div style="height: 0.75rem;"></div>', unsafe_allow_html=True)
            login_user_input = st.text_input("Username", placeholder="Enter your username", key="auth_login_user")
            login_pass_input = st.text_input("Password", placeholder="Enter your password", type="password", key="auth_login_pass")

            if st.button("Sign In to Workspace", key="btn_login_submit", type="primary"):
                if login_user_input and login_pass_input:
                    res = login_user(login_user_input, login_pass_input)
                    if res["success"]:
                        st.session_state.logged_in = True
                        st.session_state.username = res["username"]
                        st.session_state.user_email = res.get("email", f"{res['username']}@workspace.local")
                        load_user_persistent_data(res["username"])
                        st.rerun()
                    else:
                        st.error(res["message"])
                else:
                    st.warning("Please fill in both username and password.")

        with tab_signup:
            st.markdown('<div style="height: 0.75rem;"></div>', unsafe_allow_html=True)
            reg_user_input = st.text_input("Choose Username", placeholder="Enter a username", key="auth_reg_user")
            reg_email_input = st.text_input("Email Address", placeholder="name@organization.com", key="auth_reg_email")
            reg_pass_input = st.text_input("Choose Password", placeholder="Minimum 6 characters", type="password", key="auth_reg_pass")
            reg_confirm_input = st.text_input("Confirm Password", placeholder="Re-enter password", type="password", key="auth_reg_confirm")

            if st.button("Create Account", key="btn_reg_submit", type="primary"):
                if reg_user_input and reg_email_input and reg_pass_input and reg_confirm_input:
                    if reg_pass_input != reg_confirm_input:
                        st.error("Passwords do not match.")
                    elif len(reg_pass_input) < 6:
                        st.error("Password must be at least 6 characters long.")
                    else:
                        res = register_user(reg_user_input, reg_email_input, reg_pass_input)
                        if res["success"]:
                            st.success("Account created successfully! Please sign in.")
                        else:
                            st.error(res["message"])
                else:
                    st.warning("Please fill in all required fields.")

        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()


# Ensure persistent data is loaded for active user
if not st.session_state.history and st.session_state.username:
    st.session_state.history = fetch_user_history(st.session_state.username)
if not st.session_state.saved_results and st.session_state.username:
    st.session_state.saved_results = fetch_user_saved_notes(st.session_state.username)


# ==============================================================================
# SIDEBAR NAVIGATION & USER FOOTER
# ==============================================================================
with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-header">
        {render_icon("search", 22, "#818cf8")}
        <div>
            <div class="sidebar-brand">NeuroSearch</div>
            <div class="sidebar-sub">Knowledge Platform</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    views = [
        ("home", "Home", "home"),
        ("search", "Search", "search"),
        ("sources", "Sources", "sources"),
        ("saved", "Saved", "saved"),
        ("history", "Chat History", "history"),
        ("pdf_upload", "Upload PDF", "upload"),
        ("wiki_explorer", "Wiki Explorer", "explorer"),
        ("settings", "Settings", "settings"),
    ]

    for v_id, v_label, v_icon in views:
        is_active = st.session_state.active_view == v_id
        btn_type = "primary" if is_active else "secondary"
        if st.button(f"{v_label}", key=f"nav_btn_{v_id}", use_container_width=True, type=btn_type):
            st.session_state.active_view = v_id
            st.rerun()

    st.markdown('<div style="margin-top: 1.5rem; border-top: 1px solid #1e293b; padding-top: 1rem;"></div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background-color: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 0.75rem 0.85rem; margin-bottom: 0.75rem;">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <div style="width: 30px; height: 30px; border-radius: 50%; background-color: #1e1b4b; border: 1px solid #4338ca; display: flex; align-items: center; justify-content: center; font-weight: 600; color: #a5b4fc; font-size: 0.75rem;">
                    {st.session_state.username[:2].upper()}
                </div>
                <div>
                    <div style="font-size: 0.825rem; font-weight: 600; color: #f8fafc;">{st.session_state.username}</div>
                    <div style="font-size: 0.7rem; color: #64748b;">Enterprise Workspace</div>
                </div>
            </div>
            <span class="badge badge-indigo">Active</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Sign Out", key="nav_logout_btn", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


# ==============================================================================
# TOP HEADER BAR
# ==============================================================================
current_view_title = st.session_state.active_view.replace("_", " ").title()
st.markdown(f"""
<div class="top-header">
    <div style="display: flex; align-items: center; gap: 8px;">
        <span style="color: #64748b; font-size: 0.85rem;">Workspace</span>
        <span style="color: #334155; font-size: 0.85rem;">/</span>
        <span style="color: #f8fafc; font-size: 0.85rem; font-weight: 600;">{current_view_title}</span>
    </div>
    <div style="display: flex; align-items: center; gap: 10px;">
        <span class="badge badge-indigo">
            {render_icon("cpu", 13, "#a5b4fc")} Groq LLaMA3
        </span>
        <span class="badge badge-slate">
            {render_icon("database", 13, "#94a3b8")} BM25 + FAISS
        </span>
    </div>
</div>
""", unsafe_allow_html=True)


# Core Execution Helper for Search
def execute_search_query(query_text: str, search_mode: str):
    if not query_text.strip():
        return

    st.session_state.pending_query = ""
    t0 = time.time()

    docs, llm, prompt, vectorstore, err_msg = get_cached_components()

    if search_mode == "pdf":
        if not st.session_state.pdf_vectorstore:
            st.error("No PDF document loaded. Please upload a PDF file in the Upload PDF section.")
            return
        if not llm:
            st.error(f"GROQ_API_KEY environment variable is not configured. ({err_msg})")
            return
        res = ask_pdf(query_text, st.session_state.pdf_vectorstore, llm, prompt)
        answer = res["answer"]
        sources = res["sources"]
    else:
        k_val = st.session_state.get("top_k", 5)
        results = hybrid_search(query_text, docs, vectorstore, k=k_val)
        sources = list(set([d.metadata["title"] for d in results]))

        if llm:
            context = "\n\n".join([d.page_content for d in results])
            chain = prompt | llm
            response = chain.invoke({"context": context, "question": query_text})
            answer = response.content
        else:
            answer = "GROQ_API_KEY environment variable is not configured. Here are the top retrieved sources:\n\n" + \
                     "\n\n".join([f"**{d.metadata['title']}**:\n{d.page_content[:300]}..." for d in results])

    elapsed = round(time.time() - t0, 2)

    result_payload = {
        "id": str(uuid.uuid4()),
        "query": query_text,
        "answer": answer,
        "sources": sources,
        "time": elapsed,
        "mode": search_mode,
        "timestamp": time.strftime("%b %d, %H:%M")
    }

    # Save to SQLite database history
    save_history_entry(st.session_state.username, result_payload)
    st.session_state.history = fetch_user_history(st.session_state.username)

    st.session_state.current_search_result = result_payload
    st.session_state.active_view = "search"
    st.rerun()


# Check if pending query triggered from home topic click
if st.session_state.pending_query:
    execute_search_query(st.session_state.pending_query, st.session_state.search_mode)


# ==============================================================================
# VIEW 1: HOME / DASHBOARD
# ==============================================================================
if st.session_state.active_view == "home":
    st.markdown("""
    <div style="margin-bottom: 1.75rem;">
        <h1 class="page-heading" style="font-size: 1.85rem;">Search the knowledge you need.</h1>
        <p class="page-description">Find relevant information across indexed Wikipedia articles, research topics, and uploaded PDF documents.</p>
    </div>
    """, unsafe_allow_html=True)

    # Integrated Search Card
    st.markdown('<div class="saas-card">', unsafe_allow_html=True)
    
    col_mode1, col_mode2, _ = st.columns([1.5, 1.5, 4])
    with col_mode1:
        if st.button("Wiki Knowledge", type="primary" if st.session_state.search_mode == "wiki" else "secondary", key="home_mode_wiki"):
            st.session_state.search_mode = "wiki"
            st.rerun()
    with col_mode2:
        if st.button("PDF Document", type="primary" if st.session_state.search_mode == "pdf" else "secondary", key="home_mode_pdf"):
            st.session_state.search_mode = "pdf"
            st.rerun()

    st.markdown('<div style="height: 0.75rem;"></div>', unsafe_allow_html=True)

    c_input, c_btn = st.columns([5.5, 1])
    with c_input:
        placeholder = "Ask about your uploaded PDF document..." if st.session_state.search_mode == "pdf" else "Ask anything about Machine Learning, AI, LLMs..."
        home_query = st.text_input("Global Search Input", placeholder=placeholder, label_visibility="collapsed", key="input_home_query")
    with c_btn:
        home_submit = st.button("Search", key="btn_home_search", type="primary")

    if home_submit and home_query:
        execute_search_query(home_query, st.session_state.search_mode)

    st.markdown('</div>', unsafe_allow_html=True)

    # Topic Exploration Grid
    st.markdown("""
    <div style="margin-top: 2rem; margin-bottom: 1rem; display: flex; align-items: center; justify-content: space-between;">
        <div style="font-size: 1.05rem; font-weight: 600; color: #f8fafc;">Explore Core Topics</div>
        <div style="font-size: 0.8rem; color: #64748b;">Click any topic to query immediately</div>
    </div>
    """, unsafe_allow_html=True)

    topics = [
        ("Artificial Intelligence", "Concepts, history, and foundational models", "What is Artificial Intelligence?"),
        ("Machine Learning", "Algorithms, supervised learning, and evaluation", "Explain Machine Learning fundamentals"),
        ("Deep Learning", "Neural network architectures and deep networks", "Explain deep learning and neural networks"),
        ("Natural Language Processing", "LLMs, text analysis, and semantic understanding", "What is Natural Language Processing?"),
        ("Transformers", "Self-attention mechanisms and transformer models", "How do transformer models work?"),
        ("Retrieval-Augmented Generation", "RAG architectures, vector DBs, and hybrid search", "What is Retrieval-Augmented Generation?"),
    ]

    t_col1, t_col2 = st.columns(2)
    for idx, (t_name, t_desc, t_q) in enumerate(topics):
        col_target = t_col1 if idx % 2 == 0 else t_col2
        with col_target:
            st.markdown(f"""
            <div style="background-color: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 1rem; margin-bottom: 0.75rem;">
                <div style="font-size: 0.95rem; font-weight: 600; color: #f8fafc;">{t_name}</div>
                <div style="font-size: 0.825rem; color: #94a3b8; margin-top: 0.25rem; margin-bottom: 0.75rem;">{t_desc}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Search {t_name}", key=f"topic_btn_{idx}"):
                execute_search_query(t_q, "wiki")

    # Recent Searches
    if st.session_state.history:
        st.markdown("""
        <div style="margin-top: 2rem; margin-bottom: 0.75rem; font-size: 1.05rem; font-weight: 600; color: #f8fafc;">
            Recent Searches
        </div>
        """, unsafe_allow_html=True)

        for idx, h_item in enumerate(st.session_state.history[:4]):
            col_h1, col_h2 = st.columns([5, 1])
            with col_h1:
                st.markdown(f"""
                <div style="background-color: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 0.65rem 0.85rem; margin-bottom: 0.5rem; display: flex; align-items: center; justify-content: space-between;">
                    <div style="font-size: 0.875rem; color: #e2e8f0;">{h_item['query']}</div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span class="badge badge-slate">{h_item['mode'].upper()}</span>
                        <span style="font-size: 0.75rem; color: #64748b;">{h_item['timestamp']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col_h2:
                if st.button("Re-run", key=f"rerun_home_{idx}"):
                    execute_search_query(h_item['query'], h_item['mode'])


# ==============================================================================
# VIEW 2: SEARCH RESULTS
# ==============================================================================
elif st.session_state.active_view == "search":
    st.markdown("""
    <div style="margin-bottom: 1.25rem;">
        <h1 class="page-heading">Search Results & Synthesis</h1>
        <p class="page-description">Source-backed answers powered by hybrid BM25 + FAISS retrieval.</p>
    </div>
    """, unsafe_allow_html=True)

    # Search Bar
    st.markdown('<div class="saas-card">', unsafe_allow_html=True)
    c_input, c_btn = st.columns([5.5, 1])
    with c_input:
        search_query_val = st.text_input("Query Input", value=st.session_state.current_search_result["query"] if st.session_state.current_search_result else "", label_visibility="collapsed", key="input_results_query")
    with c_btn:
        search_submit = st.button("Search", key="btn_results_search", type="primary")

    if search_submit and search_query_val:
        execute_search_query(search_query_val, st.session_state.search_mode)

    st.markdown('</div>', unsafe_allow_html=True)

    res = st.session_state.current_search_result
    if res:
        # Answer Card
        st.markdown(f"""
        <div class="saas-card">
            <div class="saas-card-header">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 0.95rem; font-weight: 600; color: #f8fafc;">Synthesized Answer</span>
                    <span class="badge badge-indigo">Groq LLaMA3</span>
                </div>
                <span style="font-size: 0.75rem; color: #64748b;">Latency: {res['time']}s</span>
            </div>
            <div style="font-size: 0.925rem; line-height: 1.7; color: #cbd5e1; margin-bottom: 1rem;">
                {res['answer']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_act1, col_act2, _ = st.columns([1.5, 1.5, 4])
        with col_act1:
            if st.button("Save Result", key="btn_save_current_res"):
                if not any(s["id"] == res["id"] for s in st.session_state.saved_results):
                    save_research_note(st.session_state.username, res)
                    st.session_state.saved_results = fetch_user_saved_notes(st.session_state.username)
                    st.success("Saved to your persistent workspace research notes!")
                else:
                    st.info("Already saved in your notes.")
        with col_act2:
            if st.button("Copy Markdown", key="btn_copy_ans"):
                st.code(res['answer'], language="markdown")

        # Source Citations
        st.markdown(f"""
        <div style="margin-top: 2rem; margin-bottom: 0.75rem; display: flex; align-items: center; justify-content: space-between;">
            <div style="font-size: 1.05rem; font-weight: 600; color: #f8fafc;">Retrieved Sources ({len(res['sources'])})</div>
            <div style="font-size: 0.8rem; color: #64748b;">Verified context chunks</div>
        </div>
        """, unsafe_allow_html=True)

        for s_idx, src in enumerate(res["sources"]):
            col_src1, col_src2 = st.columns([5, 1.2])
            with col_src1:
                st.markdown(f"""
                <div class="source-card">
                    <div class="source-title">{src}</div>
                    <div class="source-snippet">Cited in response synthesis for verification and source trace.</div>
                </div>
                """, unsafe_allow_html=True)
            with col_src2:
                if st.button("Inspect Source", key=f"btn_inspect_src_{s_idx}"):
                    st.session_state.target_source_title = src
                    st.session_state.active_view = "wiki_explorer"
                    st.rerun()
    else:
        st.info("Enter a query above or choose a topic from Home to generate answers.")


# ==============================================================================
# VIEW 3: SOURCES
# ==============================================================================
elif st.session_state.active_view == "sources":
    st.markdown("""
    <div style="margin-bottom: 1.25rem;">
        <h1 class="page-heading">Indexed Knowledge Base</h1>
        <p class="page-description">Document repository and vector embeddings used for hybrid retrieval.</p>
    </div>
    """, unsafe_allow_html=True)

    docs = get_all_db_documents()

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="saas-card" style="text-align: center;">
            <div style="font-size: 1.5rem; font-weight: 700; color: #f8fafc;">{len(docs)}</div>
            <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 0.2rem;">Indexed Articles</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown("""
        <div class="saas-card" style="text-align: center;">
            <div style="font-size: 1.5rem; font-weight: 700; color: #f8fafc;">756</div>
            <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 0.2rem;">FAISS Vector Chunks</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown("""
        <div class="saas-card" style="text-align: center;">
            <div style="font-size: 0.9rem; font-weight: 600; color: #a5b4fc; margin-top: 0.4rem;">all-MiniLM-L6-v2</div>
            <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 0.2rem;">Embedding Model</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown("""
        <div class="saas-card" style="text-align: center;">
            <div style="font-size: 0.9rem; font-weight: 600; color: #a5b4fc; margin-top: 0.4rem;">BM25 + FAISS (RRF)</div>
            <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 0.2rem;">Retrieval Engine</div>
        </div>
        """, unsafe_allow_html=True)

    src_filter = st.text_input("Filter Sources", placeholder="Search document title or URL...", key="src_filter_input")

    filtered_docs = [d for d in docs if src_filter.lower() in d["title"].lower() or src_filter.lower() in d["url"].lower()] if src_filter else docs

    for d in filtered_docs:
        with st.expander(f"{d['title']} ({len(d['content'])} characters)"):
            st.markdown(f"**Source URL:** [{d['url']}]({d['url']})")
            st.markdown("**Content Excerpt:**")
            st.text(d['content'][:800] + "..." if len(d['content']) > 800 else d['content'])


# ==============================================================================
# VIEW 4: SAVED ANSWERS
# ==============================================================================
elif st.session_state.active_view == "saved":
    st.markdown("""
    <div style="margin-bottom: 1.25rem;">
        <h1 class="page-heading">Saved Results & Research Notes</h1>
        <p class="page-description">Bookmarked answers and cited references saved permanently in your account.</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.saved_results:
        st.markdown("""
        <div class="saas-card" style="text-align: center; padding: 3rem 1.5rem;">
            <div style="font-size: 1.1rem; font-weight: 600; color: #f8fafc; margin-bottom: 0.5rem;">No saved notes yet</div>
            <div style="font-size: 0.875rem; color: #94a3b8;">Bookmark answers from the search results page to store them permanently here.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for idx, item in enumerate(st.session_state.saved_results):
            st.markdown(f"""
            <div class="saas-card">
                <div class="saas-card-header">
                    <div style="font-size: 1.05rem; font-weight: 600; color: #f8fafc;">{item['query']}</div>
                    <span class="badge badge-indigo">{item['mode'].upper()}</span>
                </div>
                <div style="font-size: 0.9rem; line-height: 1.6; color: #cbd5e1; margin-bottom: 0.75rem;">
                    {item['answer']}
                </div>
                <div style="font-size: 0.75rem; color: #64748b;">
                    Saved on: {item['timestamp']} · Sources: {", ".join(item['sources'])}
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_s1, col_s2, _ = st.columns([1.5, 1.5, 4])
            with col_s1:
                if st.button("Copy Text", key=f"btn_copy_saved_{idx}"):
                    st.code(item['answer'], language="markdown")
            with col_s2:
                if st.button("Remove Note", key=f"btn_rem_saved_{idx}"):
                    delete_saved_note(st.session_state.username, item["id"])
                    st.session_state.saved_results = fetch_user_saved_notes(st.session_state.username)
                    st.rerun()


# ==============================================================================
# VIEW 5: CHAT HISTORY
# ==============================================================================
elif st.session_state.active_view == "history":
    st.markdown("""
    <div style="margin-bottom: 1.25rem;">
        <h1 class="page-heading">Query History</h1>
        <p class="page-description">Review past search queries and retrieval sessions.</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.history:
        st.markdown("""
        <div class="saas-card" style="text-align: center; padding: 3rem 1.5rem;">
            <div style="font-size: 1.1rem; font-weight: 600; color: #f8fafc; margin-bottom: 0.5rem;">No query history yet</div>
            <div style="font-size: 0.875rem; color: #94a3b8;">Your query sessions and generated answers will appear here.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        if st.button("Clear All History", key="btn_clear_all_history"):
            clear_user_history(st.session_state.username)
            st.session_state.history = []
            st.rerun()

        st.markdown('<div style="height: 0.5rem;"></div>', unsafe_allow_html=True)

        for idx, h in enumerate(st.session_state.history):
            with st.expander(f"{h['query']} — ({h['timestamp']})"):
                st.markdown(f"**Mode:** {h['mode'].upper()} | **Latency:** {h['time']}s")
                st.markdown("**Answer:**")
                st.markdown(h['answer'])
                st.markdown("**Sources:** " + ", ".join(h['sources']))

                if st.button("Re-open Query Result", key=f"btn_reopen_hist_{idx}"):
                    st.session_state.current_search_result = h
                    st.session_state.active_view = "search"
                    st.rerun()


# ==============================================================================
# VIEW 6: UPLOAD PDF
# ==============================================================================
elif st.session_state.active_view == "pdf_upload":
    st.markdown("""
    <div style="margin-bottom: 1.25rem;">
        <h1 class="page-heading">PDF Document Research</h1>
        <p class="page-description">Upload custom PDF documents to perform semantic vector search and RAG answering.</p>
    </div>
    """, unsafe_allow_html=True)

    uploaded_pdf = st.file_uploader("Upload PDF Document", type=["pdf"], key="pdf_file_uploader")

    if uploaded_pdf:
        if st.session_state.pdf_name != uploaded_pdf.name:
            with st.spinner("Processing & embedding PDF document..."):
                st.session_state.pdf_vectorstore = process_pdf(uploaded_pdf)
                st.session_state.pdf_name = uploaded_pdf.name
            st.success(f"PDF '{uploaded_pdf.name}' processed and ready for questions!")

    if st.session_state.pdf_name:
        st.markdown(f"""
        <div class="saas-card" style="border-left: 3px solid #6366f1;">
            <div style="font-size: 0.95rem; font-weight: 600; color: #f8fafc;">Active Document: {st.session_state.pdf_name}</div>
            <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 0.25rem;">FAISS Vector Index active in memory</div>
        </div>
        """, unsafe_allow_html=True)

        pdf_query = st.text_input("Ask a question about this PDF", placeholder="e.g. What are the key findings in section 3?", key="pdf_ask_input")
        if st.button("Ask PDF", key="btn_ask_pdf_submit", type="primary") and pdf_query:
            execute_search_query(pdf_query, "pdf")


# ==============================================================================
# VIEW 7: WIKI EXPLORER
# ==============================================================================
elif st.session_state.active_view == "wiki_explorer":
    st.markdown("""
    <div style="margin-bottom: 1.25rem;">
        <h1 class="page-heading">Wikipedia Knowledge Explorer</h1>
        <p class="page-description">Inspect curated AI & ML Wikipedia articles stored in the local database.</p>
    </div>
    """, unsafe_allow_html=True)

    docs = get_all_db_documents()
    doc_titles = [d["title"] for d in docs]

    default_index = 0
    if st.session_state.target_source_title in doc_titles:
        default_index = doc_titles.index(st.session_state.target_source_title)
        st.session_state.target_source_title = None

    selected_title = st.selectbox("Select Wikipedia Article to Inspect", options=doc_titles, index=default_index, key="wiki_select_title")
    selected_doc = next((d for d in docs if d["title"] == selected_title), None)

    if selected_doc:
        st.markdown(f"""
        <div class="saas-card">
            <div class="saas-card-header">
                <div style="font-size: 1.2rem; font-weight: 700; color: #f8fafc;">{selected_doc['title']}</div>
                <span class="badge badge-indigo">{len(selected_doc['content'])} chars</span>
            </div>
            <div style="font-size: 0.825rem; color: #818cf8; margin-bottom: 1rem;">
                URL: <a href="{selected_doc['url']}" target="_blank" style="color: #818cf8;">{selected_doc['url']}</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"Search RAG for '{selected_doc['title']}'", key="btn_search_this_wiki"):
            execute_search_query(f"Explain {selected_doc['title']}", "wiki")

        st.markdown("### Article Content Preview")
        st.text_area("Full Article Text", value=selected_doc['content'], height=350, key="wiki_text_area")


# ==============================================================================
# VIEW 8: SETTINGS
# ==============================================================================
elif st.session_state.active_view == "settings":
    st.markdown("""
    <div style="margin-bottom: 1.25rem;">
        <h1 class="page-heading">Workspace Settings</h1>
        <p class="page-description">Configure retrieval parameters, model options, and view system health.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="saas-card">', unsafe_allow_html=True)
    st.markdown('<div class="saas-title">Retrieval Parameters</div>', unsafe_allow_html=True)
    
    new_top_k = st.slider("Top-K Context Chunks to Retrieve", min_value=3, max_value=10, value=st.session_state.top_k, step=1, key="settings_top_k_slider")
    st.session_state.top_k = new_top_k

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="saas-card">
        <div class="saas-title">Model & System Information</div>
        <div style="font-size: 0.875rem; color: #cbd5e1; margin-top: 0.5rem; line-height: 1.8;">
            • <b>LLM Generation:</b> Groq LLaMA3 (llama-3.3-70b-versatile)<br>
            • <b>Dense Vector Embeddings:</b> sentence-transformers/all-MiniLM-L6-v2<br>
            • <b>Hybrid Retrieval:</b> BM25 (Rank-BM25) + FAISS CPU (Reciprocal Rank Fusion)<br>
            • <b>Storage:</b> SQLite (data.db & users.db)<br>
            • <b>Deployment:</b> Single-service Docker on Hugging Face Spaces (Port 7860)
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="saas-card">
        <div class="saas-title">Account Details</div>
    """, unsafe_allow_html=True)
    st.write(f"**Username:** {st.session_state.username}")
    st.write(f"**Email:** {st.session_state.user_email}")
    st.markdown('</div>', unsafe_allow_html=True)