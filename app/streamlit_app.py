import os
import sys
import time
import uuid
import datetime
import sqlite3
import streamlit as st

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ui_styles import CSS_STYLES
from app.icons import render_icon
from app.auth import (
    init_users_db,
    login_user,
    register_user,
    save_history_entry,
    fetch_user_history,
    clear_user_history,
    save_research_note,
    fetch_user_saved_notes,
    delete_saved_note,
)
from app.rag.rag_chain import load_chunks_from_db, build_rag_chain, hybrid_search, ask
from app.pdf_handler import process_pdf, ask_pdf

# -------------------------------------------------------------------
# Page Config & Styles
# -------------------------------------------------------------------
st.set_page_config(
    page_title="NeuroSearch | Hybrid Knowledge Engine",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(CSS_STYLES, unsafe_allow_html=True)
init_users_db()

# -------------------------------------------------------------------
# Session State Management
# -------------------------------------------------------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "active_view" not in st.session_state:
    st.session_state.active_view = "Home"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "search_mode" not in st.session_state:
    st.session_state.search_mode = "Wiki"
if "pdf_vectorstore" not in st.session_state:
    st.session_state.pdf_vectorstore = None
if "pdf_file_name" not in st.session_state:
    st.session_state.pdf_file_name = None

# Cache expensive resources
@st.cache_resource
def get_cached_wiki_docs():
    return load_chunks_from_db()

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DB_PATH = os.path.join(PROJECT_ROOT, "data.db")

def get_knowledge_base_stats():
    """Dynamically read article count and chunk count from knowledge base."""
    try:
        conn = sqlite3.connect(DATA_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        doc_count = cursor.fetchone()[0]
        conn.close()
    except Exception as e:
        doc_count = 0
        
    try:
        docs = get_cached_wiki_docs()
        chunk_count = len(docs)
    except Exception:
        chunk_count = 0
        
    return doc_count, chunk_count


# -------------------------------------------------------------------
# Authentication Screen
# -------------------------------------------------------------------
def render_auth_page():
    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.8, 1])
    
    with col2:
        st.markdown(
            f"""
            <div class="saas-card" style="text-align: center; padding: 2.5rem 2rem; border-color: #334155;">
                <div style="font-size: 1.8rem; font-weight: 700; color: #f8fafc; letter-spacing: -0.02em; margin-bottom: 0.25rem;">
                    NeuroSearch
                </div>
                <div style="font-size: 0.875rem; color: #94a3b8; margin-bottom: 1.5rem;">
                    Hybrid Retrieval-Augmented Research Platform
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        tab_login, tab_register = st.tabs(["Sign In", "Create Account"])
        
        with tab_login:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            login_user_input = st.text_input("Username", key="auth_login_user")
            login_pass_input = st.text_input("Password", type="password", key="auth_login_pass")
            
            if st.button("Sign In to Workspace", use_container_width=True, type="primary"):
                if not login_user_input or not login_pass_input:
                    st.error("Please provide both username and password.")
                else:
                    res = login_user(login_user_input, login_pass_input)
                    if res["success"]:
                        st.session_state.user = {"username": res["username"], "email": res["email"]}
                        st.success("Signed in successfully!")
                        time.sleep(0.3)
                        st.rerun()
                    else:
                        st.error(res["message"])
                        
        with tab_register:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            reg_user = st.text_input("Choose Username", key="auth_reg_user")
            reg_email = st.text_input("Email Address", key="auth_reg_email")
            reg_pass = st.text_input("Create Password", type="password", key="auth_reg_pass")
            
            if st.button("Create Account", use_container_width=True):
                if not reg_user or not reg_email or not reg_pass:
                    st.error("Please fill in all registration fields.")
                else:
                    res = register_user(reg_user, reg_email, reg_pass)
                    if res["success"]:
                        st.success("Account created! You may now sign in.")
                    else:
                        st.error(res["message"])

if not st.session_state.user:
    render_auth_page()
    st.stop()

# -------------------------------------------------------------------
# Sidebar Component
# -------------------------------------------------------------------
def render_sidebar():
    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-header">
                <div>
                    <div class="sidebar-brand">NeuroSearch</div>
                    <div class="sidebar-sub">Enterprise Knowledge</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # New Chat Action Button (Clears active conversation completely)
        if st.button("+ New Chat", use_container_width=True, type="primary"):
            st.session_state.messages = []
            st.session_state.active_view = "Search"
            st.rerun()
            
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        nav_items = [
            ("Home", "Home"),
            ("Search Workspace", "Search"),
            ("Indexed Sources", "Sources"),
            ("Saved Answers", "Saved Answers"),
            ("Chat History", "Chat History"),
            ("Upload PDF Studio", "Upload PDF"),
            ("Wiki Explorer", "Wiki Explorer"),
            ("Platform Settings", "Settings"),
        ]
        
        for label, view_key in nav_items:
            is_active = st.session_state.active_view == view_key
            button_kind = "primary" if is_active else "secondary"
            if st.button(label, key=f"nav_{view_key}", use_container_width=True, type=button_kind):
                st.session_state.active_view = view_key
                st.rerun()
                
        st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
        st.markdown("<hr style='border-color: #1e293b; margin: 0 0 12px 0;'>", unsafe_allow_html=True)
        
        # User Profile Footer
        st.markdown(
            f"""
            <div style="padding: 0 4px; margin-bottom: 8px;">
                <div style="font-size: 0.85rem; font-weight: 600; color: #e2e8f0;">{st.session_state.user['username']}</div>
                <div style="font-size: 0.725rem; color: #64748b;">{st.session_state.user['email']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        if st.button("Log Out", use_container_width=True):
            st.session_state.user = None
            st.session_state.messages = []
            st.rerun()

render_sidebar()

# -------------------------------------------------------------------
# RAG Execution Helper
# -------------------------------------------------------------------
def execute_rag_query(query_text: str):
    user_name = st.session_state.user["username"]
    search_mode = st.session_state.search_mode
    
    # 1. Add User Message
    st.session_state.messages.append({
        "id": str(uuid.uuid4()),
        "role": "user",
        "content": query_text,
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
    })
    
    start_time = time.time()
    
    # 2. History Context for Follow-ups
    history_context = ""
    if len(st.session_state.messages) > 1:
        prev_user_msgs = [m["content"] for m in st.session_state.messages[:-1] if m["role"] == "user"]
        if prev_user_msgs:
            history_context = prev_user_msgs[-1]
            
    # 3. Perform Retrieval & LLM Generation
    with st.status("Searching knowledge base & generating answer...", expanded=True) as status:
        st.write("Initializing retrieval pipeline...")
        
        if search_mode == "Wiki":
            st.write("Performing hybrid BM25 + FAISS search...")
            res = ask(query_text, history_context=history_context)
            answer = res["answer"]
            sources = res["sources"]
            rich_sources = res.get("rich_sources", [])
            raw_docs = res.get("raw_docs", [])
        else: # PDF Mode
            st.write("Querying attached PDF document vector store...")
            if not st.session_state.pdf_vectorstore:
                answer = "No PDF document attached. Please upload a PDF file using the attachment uploader above."
                sources = []
                rich_sources = []
                raw_docs = []
            else:
                groq_key = os.getenv("GROQ_API_KEY")
                llm, prompt, _ = build_rag_chain(api_key=groq_key) if groq_key else (None, None, None)
                res = ask_pdf(query_text, st.session_state.pdf_vectorstore, llm, prompt)
                answer = res["answer"]
                sources = res["sources"]
                rich_sources = [{"title": f"{st.session_state.pdf_file_name} ({s})", "url": "", "snippet": ""} for s in sources]
                raw_docs = []
                    
        st.write("Response generated!")
        status.update(label="Query complete", state="complete", expanded=False)
        
    latency = round(time.time() - start_time, 2)
    
    # 4. Save Entry to History Database
    entry = {
        "id": str(uuid.uuid4()),
        "query": query_text,
        "answer": answer,
        "sources": sources,
        "time": latency,
        "mode": search_mode,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_history_entry(user_name, entry)
    
    # 5. Append Assistant Message (Sources bound ONLY to this specific message object)
    st.session_state.messages.append({
        "id": entry["id"],
        "role": "assistant",
        "content": answer,
        "sources": sources,
        "rich_sources": rich_sources,
        "raw_docs": raw_docs,
        "latency": latency,
        "mode": search_mode,
        "timestamp": entry["timestamp"]
    })

# -------------------------------------------------------------------
# VIEW: Home Dashboard
# -------------------------------------------------------------------
def render_home_view():
    st.markdown(
        """
        <div class="top-header">
            <div>
                <h1 class="page-heading">Platform Overview</h1>
                <div class="page-description">Enterprise hybrid knowledge discovery & neural document search dashboard.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Read Dynamic Article and Chunk Counts
    doc_count, chunk_count = get_knowledge_base_stats()
    username = st.session_state.user["username"]
    notes_count = len(fetch_user_saved_notes(username))
    has_groq_key = bool(os.getenv("GROQ_API_KEY"))
    
    # Metric Summary Cards
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.markdown(
            f"""
            <div class="saas-card">
                <div style="font-size: 0.75rem; color: #94a3b8; font-weight: 500;">Knowledge Base</div>
                <div style="font-size: 1.4rem; font-weight: 700; color: #f8fafc; margin-top: 4px;">{doc_count} articles</div>
                <div style="font-size: 0.725rem; color: #818cf8; margin-top: 4px;">{chunk_count} searchable chunks</div>
                <div style="font-size: 0.7rem; color: #64748b; margin-top: 6px; line-height: 1.2;">Pre-indexed Wikipedia knowledge available for hybrid search.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_m2:
        st.markdown(
            """
            <div class="saas-card">
                <div style="font-size: 0.75rem; color: #94a3b8; font-weight: 500;">Vector Engine</div>
                <div style="font-size: 1.4rem; font-weight: 700; color: #f8fafc; margin-top: 4px;">FAISS + BM25</div>
                <div style="font-size: 0.725rem; color: #34d399; margin-top: 4px;">Hybrid RRF Merging</div>
                <div style="font-size: 0.7rem; color: #64748b; margin-top: 6px; line-height: 1.2;">Dense vector + sparse keyword retrieval.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_m3:
        status_badge = '<span style="color: #34d399;">● Connected</span>' if has_groq_key else '<span style="color: #fb7185;">○ Not configured</span>'
        st.markdown(
            f"""
            <div class="saas-card">
                <div style="font-size: 0.75rem; color: #94a3b8; font-weight: 500;">Synthesis Model</div>
                <div style="font-size: 1.4rem; font-weight: 700; color: #f8fafc; margin-top: 4px;">Llama 3.3 70B</div>
                <div style="font-size: 0.725rem; margin-top: 4px;">{status_badge}</div>
                <div style="font-size: 0.7rem; color: #64748b; margin-top: 6px; line-height: 1.2;">Groq High-Speed API (groq/compound).</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_m4:
        st.markdown(
            f"""
            <div class="saas-card">
                <div style="font-size: 0.75rem; color: #94a3b8; font-weight: 500;">Saved Research</div>
                <div style="font-size: 1.4rem; font-weight: 700; color: #f8fafc; margin-top: 4px;">{notes_count} notes</div>
                <div style="font-size: 0.725rem; color: #f43f5e; margin-top: 4px;">Local SQLite Store</div>
                <div style="font-size: 0.7rem; color: #64748b; margin-top: 6px; line-height: 1.2;">Bookmarked citations and answers.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    
    # Launch Workspace Card (Clean Call-to-Action)
    st.markdown(
        """
        <div class="saas-card" style="padding: 2rem; border-color: #3730a3; background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%);">
            <div style="font-size: 1.3rem; font-weight: 700; color: #f8fafc; margin-bottom: 0.4rem;">
                Start Conversational Research
            </div>
            <div style="font-size: 0.85rem; color: #cbd5e1; max-width: 650px; margin-bottom: 1.25rem; line-height: 1.5;">
                Ask questions across pre-indexed Wikipedia knowledge stores or upload custom PDF research papers for instant document retrieval.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        if st.button("Launch Wikipedia Hybrid Search", use_container_width=True, type="primary"):
            st.session_state.search_mode = "Wiki"
            st.session_state.active_view = "Search"
            st.rerun()
    with col_c2:
        if st.button("Attach & Search PDF Document", use_container_width=True):
            st.session_state.search_mode = "PDF"
            st.session_state.active_view = "Search"
            st.rerun()

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    
    # Recent Query Log Overview (Summary only, NO retrieved sources or active answers!)
    st.markdown("<div style='font-size: 1.05rem; font-weight: 600; color: #f8fafc; margin-bottom: 10px;'>Recent Research Activity</div>", unsafe_allow_html=True)
    recent_history = fetch_user_history(username)[:3]
    if not recent_history:
        st.info("No research activity recorded yet. Launch Search to get started!")
    else:
        for item in recent_history:
            st.markdown(
                f"""
                <div class="saas-card">
                    <div class="saas-card-header">
                        <div class="saas-title">{item['query']}</div>
                        <span class="badge badge-slate">{item['mode']} Mode</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #94a3b8;">Executed: {item['timestamp']} ({item['time']}s latency)</div>
                </div>
                """,
                unsafe_allow_html=True
            )

# -------------------------------------------------------------------
# VIEW: Conversational Search Workspace
# -------------------------------------------------------------------
def render_search_workspace():
    st.markdown(
        """
        <div class="top-header">
            <div>
                <h1 class="page-heading">Search Workspace</h1>
                <div class="page-description">Ask questions, attach PDFs, and explore cited research responses.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Search Mode & Controls
    col_mode1, col_mode2, col_clear = st.columns([1.5, 1.5, 5])
    with col_mode1:
        if st.button("Wiki Mode", type="primary" if st.session_state.search_mode == "Wiki" else "secondary", use_container_width=True):
            st.session_state.search_mode = "Wiki"
            st.rerun()
    with col_mode2:
        if st.button("PDF Mode", type="primary" if st.session_state.search_mode == "PDF" else "secondary", use_container_width=True):
            st.session_state.search_mode = "PDF"
            st.rerun()
    with col_clear:
        if len(st.session_state.messages) > 0:
            if st.button("Clear Conversation", type="secondary"):
                st.session_state.messages = []
                st.rerun()
                
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    
    # PDF Attachment Uploader (Shown when in PDF Mode)
    if st.session_state.search_mode == "PDF":
        with st.expander("PDF Document Attachment", expanded=not bool(st.session_state.pdf_vectorstore)):
            pdf_file = st.file_uploader("Upload PDF file to index for this session", type=["pdf"], key="search_pdf_attach")
            if pdf_file is not None:
                if st.session_state.pdf_file_name != pdf_file.name:
                    with st.spinner("Embedding PDF document into vector memory..."):
                        vs = process_pdf(pdf_file)
                        st.session_state.pdf_vectorstore = vs
                        st.session_state.pdf_file_name = pdf_file.name
                        st.success(f"Attached & Embedded PDF: {pdf_file.name}")
                        
            if st.session_state.pdf_vectorstore:
                st.info(f"Attached Document: **{st.session_state.pdf_file_name}** (Ready for search)")

    # Empty State (Shown ONLY when no active conversation messages)
    if not st.session_state.messages:
        st.markdown(
            f"""
            <div class="saas-card" style="text-align: center; padding: 2.25rem 1.5rem; border-style: dashed; margin-top: 0.5rem;">
                <div style="font-size: 1.15rem; font-weight: 600; color: #f8fafc; margin-bottom: 0.5rem;">
                    {st.session_state.search_mode} Research Assistant
                </div>
                <div style="font-size: 0.85rem; color: #94a3b8; max-width: 520px; margin: 0 auto 1.25rem auto;">
                    Submit a query below. Search operates via hybrid vector + keyword matching.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("<div style='font-size: 0.825rem; font-weight: 600; color: #94a3b8; margin-bottom: 8px;'>Suggested Prompts:</div>", unsafe_allow_html=True)
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            if st.button("What is Retrieval-Augmented Generation?", use_container_width=True):
                execute_rag_query("What is Retrieval-Augmented Generation?")
                st.rerun()
        with col_p2:
            if st.button("How do Artificial Neural Networks work?", use_container_width=True):
                execute_rag_query("How do Artificial Neural Networks work?")
                st.rerun()
        with col_p3:
            if st.button("Explain Machine Learning algorithms", use_container_width=True):
                execute_rag_query("Explain Machine Learning algorithms")
                st.rerun()

    # Render Conversation Messages (Retrieved Sources appear ONLY underneath assistant messages!)
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            if msg["role"] == "assistant":
                if msg.get("sources"):
                    st.markdown("<div style='font-size: 0.825rem; font-weight: 600; color: #e2e8f0; margin-top: 10px;'>Retrieved Sources:</div>", unsafe_allow_html=True)
                    for src in msg.get("rich_sources", []):
                        st.markdown(
                            f"""
                            <div class="source-card">
                                <div class="source-title">{src['title']}</div>
                                <div class="source-snippet">{src['snippet']}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        
                col_act1, col_act2, _ = st.columns([1.2, 1.8, 5])
                with col_act1:
                    if st.button("Save Note", key=f"save_{msg['id']}"):
                        note = {
                            "id": msg["id"],
                            "query": next((m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"), "Research Answer"),
                            "answer": msg["content"],
                            "sources": msg.get("sources", []),
                            "mode": msg.get("mode", "Wiki"),
                            "timestamp": msg.get("timestamp", "")
                        }
                        save_research_note(st.session_state.user["username"], note)
                        st.success("Saved to Research Notes!")
                with col_act2:
                    with st.expander("View Raw Context"):
                        for doc_text in msg.get("raw_docs", []):
                            st.text(doc_text)
                            st.markdown("---")

    # Bottom Chat Input
    user_input = st.chat_input("Ask a research question or follow-up...")
    if user_input:
        execute_rag_query(user_input)
        st.rerun()

# -------------------------------------------------------------------
# VIEW: Sources
# -------------------------------------------------------------------
def render_sources_view():
    st.markdown(
        """
        <div class="top-header">
            <div>
                <h1 class="page-heading">Indexed Knowledge Base</h1>
                <div class="page-description">Pre-indexed Wikipedia articles stored in SQLite & FAISS vector store.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    conn = sqlite3.connect(DATA_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT url, title, content FROM documents")
    rows = cursor.fetchall()
    conn.close()

    
    st.markdown(f"<div style='font-size: 0.875rem; color: #94a3b8; margin-bottom: 1rem;'>Total Articles: <b>{len(rows)}</b></div>", unsafe_allow_html=True)
    
    for url, title, content in rows:
        st.markdown(
            f"""
            <div class="saas-card">
                <div class="saas-card-header">
                    <div class="saas-title">{title}</div>
                    <span class="badge badge-indigo">SQLite + FAISS</span>
                </div>
                <div class="saas-subtitle" style="margin-bottom: 0.75rem;">
                    {content[:280]}...
                </div>
                <div style="font-size: 0.8rem;">
                    <a href="{url}" target="_blank" style="color: #818cf8; text-decoration: none;">View Original Article &rarr;</a>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# -------------------------------------------------------------------
# VIEW: Saved Answers
# -------------------------------------------------------------------
def render_saved_answers_view():
    st.markdown(
        """
        <div class="top-header">
            <div>
                <h1 class="page-heading">Saved Research Notes</h1>
                <div class="page-description">Bookmarked research answers stored in user database.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    username = st.session_state.user["username"]
    notes = fetch_user_saved_notes(username)
    
    if not notes:
        st.info("No saved research notes yet. Click 'Save Note' under any search response to store it here.")
        return
        
    for note in notes:
        st.markdown(
            f"""
            <div class="saas-card">
                <div class="saas-card-header">
                    <div class="saas-title">{note['query']}</div>
                    <span class="badge badge-indigo">{note['mode']} Mode</span>
                </div>
                <div class="saas-subtitle" style="margin-bottom: 0.75rem; white-space: pre-wrap;">
                    {note['answer']}
                </div>
                <div style="font-size: 0.725rem; color: #64748b;">Saved: {note['timestamp']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        col_rem, _ = st.columns([1.5, 6])
        with col_rem:
            if st.button("Remove Note", key=f"del_note_{note['id']}"):
                delete_saved_note(username, note["id"])
                st.success("Note removed.")
                st.rerun()
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------------
# VIEW: Chat History
# -------------------------------------------------------------------
def render_chat_history_view():
    st.markdown(
        """
        <div class="top-header">
            <div>
                <h1 class="page-heading">Search History</h1>
                <div class="page-description">Persistent log of all executed queries and latency metrics.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    username = st.session_state.user["username"]
    history = fetch_user_history(username)
    
    if not history:
        st.info("No query history recorded yet.")
        return
        
    if st.button("Clear Complete History", type="secondary"):
        clear_user_history(username)
        st.success("History cleared.")
        st.rerun()
        
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    
    for item in history:
        st.markdown(
            f"""
            <div class="saas-card">
                <div class="saas-card-header">
                    <div class="saas-title">{item['query']}</div>
                    <div>
                        <span class="badge badge-slate">{item['mode']} Mode</span>
                        <span class="badge badge-indigo">{item['time']}s</span>
                    </div>
                </div>
                <div style="font-size: 0.8rem; color: #94a3b8; margin-bottom: 0.4rem;">
                    Sources: {', '.join(item['sources']) if item['sources'] else 'None'}
                </div>
                <div style="font-size: 0.725rem; color: #64748b;">Timestamp: {item['timestamp']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        col_rerun, _ = st.columns([1.5, 6])
        with col_rerun:
            if st.button("Rerun Query", key=f"rerun_{item['id']}"):
                st.session_state.active_view = "Search"
                execute_rag_query(item['query'])
                st.rerun()

# -------------------------------------------------------------------
# VIEW: Upload PDF Studio
# -------------------------------------------------------------------
def render_upload_pdf_view():
    st.markdown(
        """
        <div class="top-header">
            <div>
                <h1 class="page-heading">PDF Processing Studio</h1>
                <div class="page-description">Upload, chunk, embed, and manage custom PDF document vector indices.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    uploaded_file = st.file_uploader("Select PDF document to index", type=["pdf"], key="studio_pdf_uploader")
    
    if uploaded_file is not None:
        if st.session_state.pdf_file_name != uploaded_file.name:
            with st.spinner("Extracting text, chunking pages, and generating embeddings..."):
                vs = process_pdf(uploaded_file)
                st.session_state.pdf_vectorstore = vs
                st.session_state.pdf_file_name = uploaded_file.name
                st.success(f"Successfully processed PDF: {uploaded_file.name}")
                
    if st.session_state.pdf_vectorstore:
        st.markdown(
            f"""
            <div class="saas-card" style="margin-top: 1rem;">
                <div class="saas-card-header">
                    <div class="saas-title">Active PDF Document</div>
                    <span class="badge badge-indigo">FAISS Index Active</span>
                </div>
                <div class="saas-subtitle">
                    File Name: <b>{st.session_state.pdf_file_name}</b><br>
                    Embedding Model: sentence-transformers/all-MiniLM-L6-v2
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Launch PDF Search Workspace", type="primary"):
            st.session_state.search_mode = "PDF"
            st.session_state.active_view = "Search"
            st.rerun()

# -------------------------------------------------------------------
# VIEW: Wiki Explorer
# -------------------------------------------------------------------
def render_wiki_explorer_view():
    st.markdown(
        """
        <div class="top-header">
            <div>
                <h1 class="page-heading">Wiki Article Explorer</h1>
                <div class="page-description">Inspect full text content of indexed articles in SQLite data.db.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    conn = sqlite3.connect(DATA_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT title, url, content FROM documents")
    rows = cursor.fetchall()
    conn.close()

    
    titles = [r[0] for r in rows]
    selected_title = st.selectbox("Select Article", titles)
    
    if selected_title:
        article = next(r for r in rows if r[0] == selected_title)
        st.markdown(f"### {article[0]}")
        st.markdown(f"[View Wikipedia Source Page]({article[1]})")
        st.markdown("---")
        st.text_area("Full Document Text", article[2], height=420)

# -------------------------------------------------------------------
# VIEW: Platform Settings
# -------------------------------------------------------------------
def render_settings_view():
    st.markdown(
        """
        <div class="top-header">
            <div>
                <h1 class="page-heading">Platform Settings</h1>
                <div class="page-description">AI engine status, environment configuration, and system parameters.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    has_groq_key = bool(os.getenv("GROQ_API_KEY"))
    
    st.markdown("### AI Configuration")
    
    if has_groq_key:
        status_card = """
        <div class="saas-card" style="border-left: 3px solid #10b981;">
            <div class="saas-card-header">
                <div class="saas-title">Groq LLM Engine</div>
                <span class="badge" style="background-color: #064e3b; color: #34d399; border-color: #047857;">● Connected</span>
            </div>
            <div class="saas-subtitle" style="line-height: 1.6;">
                Provider: <b>Groq</b><br>
                Model: <b>Llama 3.3 70B (groq/compound)</b><br>
                Credentials: <b>Securely configured through the application environment.</b>
            </div>
        </div>
        """
    else:
        status_card = """
        <div class="saas-card" style="border-left: 3px solid #f43f5e;">
            <div class="saas-card-header">
                <div class="saas-title">Groq LLM Engine</div>
                <span class="badge" style="background-color: #4c0519; color: #fb7185; border-color: #be123c;">○ Not configured</span>
            </div>
            <div class="saas-subtitle" style="line-height: 1.6;">
                Provider: <b>Groq</b><br>
                Model: <b>Llama 3.3 70B (groq/compound)</b><br>
                AI generation is unavailable because the application administrator has not configured Groq credentials.
            </div>
        </div>
        """
    st.markdown(status_card, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### System Architecture")
    st.markdown("Retrieval Strategy: `Hybrid (FAISS Vector + BM25 Keyword)`")
    st.markdown("Embedding Model: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)")
    st.markdown("Databases: `data.db` (Knowledge Store) & `users.db` (User Sessions & History)")

# -------------------------------------------------------------------
# Router Dispatcher
# -------------------------------------------------------------------
view_map = {
    "Home": render_home_view,
    "Search": render_search_workspace,
    "Sources": render_sources_view,
    "Saved Answers": render_saved_answers_view,
    "Chat History": render_chat_history_view,
    "Upload PDF": render_upload_pdf_view,
    "Wiki Explorer": render_wiki_explorer_view,
    "Settings": render_settings_view,
}

current_renderer = view_map.get(st.session_state.active_view, render_home_view)
current_renderer()