"""
Clean Neutral Slate SaaS Theme and CSS Design System for NeuroSearch.
High contrast, zero emojis, professional typography and component alignment.
"""

CSS_STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #0b0f17 !important;
    color: #f8fafc !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    overflow-x: hidden !important;
}

* {
    box-sizing: border-box;
}

/* Global App Canvas */
.stApp {
    background-color: #0b0f17 !important;
    color: #f8fafc !important;
}

/* Container Spacing */
.main .block-container {
    padding-top: 1.25rem !important;
    padding-bottom: 3rem !important;
    max-width: 1050px !important;
    margin: 0 auto !important;
}

/* Sidebar Canvas */
[data-testid="stSidebar"] {
    background-color: #070a11 !important;
    border-right: 1px solid #1e293b !important;
}

[data-testid="stSidebar"] * {
    color: #94a3b8 !important;
}

.sidebar-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0.25rem 0 0.85rem 0;
    border-bottom: 1px solid #1e293b;
    margin-bottom: 1rem;
}

.sidebar-brand {
    font-size: 1.05rem;
    font-weight: 700;
    color: #f8fafc !important;
    letter-spacing: -0.02em;
}

.sidebar-sub {
    font-size: 0.725rem;
    color: #64748b !important;
}

/* Clean Compact Sidebar Buttons */
[data-testid="stSidebar"] .stButton > button {
    background-color: transparent !important;
    color: #94a3b8 !important;
    border: 1px solid transparent !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    text-align: left !important;
    padding: 0.45rem 0.75rem !important;
    margin-bottom: 0.2rem !important;
    transition: all 0.15s ease !important;
    width: 100% !important;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #1e293b !important;
    color: #f8fafc !important;
    border-color: #334155 !important;
}

[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background-color: #1e1b4b !important;
    color: #818cf8 !important;
    border: 1px solid #4338ca !important;
    font-weight: 600 !important;
}

/* Standard Action Buttons */
.stButton > button {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 6px;
    font-weight: 500;
    font-size: 0.875rem;
    padding: 0.45rem 0.9rem;
    transition: all 0.15s ease;
}

.stButton > button:hover {
    background-color: #334155;
    border-color: #475569;
    color: #ffffff;
}

/* Primary Accent Button */
div[data-testid="stButton"] button[kind="primary"] {
    background-color: #4f46e5 !important;
    color: #ffffff !important;
    border: 1px solid #6366f1 !important;
}

div[data-testid="stButton"] button[kind="primary"]:hover {
    background-color: #4338ca !important;
    border-color: #4f46e5 !important;
}

/* BaseWeb Input Container & Password Visibility Fix */
div[data-baseweb="input"] {
    background-color: #0f172a !important;
    border: 1px solid #334155 !important;
    border-radius: 6px !important;
    color: #f8fafc !important;
}

div[data-baseweb="input"]:focus-within {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2) !important;
}

.stTextInput input, .stTextArea textarea {
    background-color: transparent !important;
    color: #f8fafc !important;
    font-size: 0.9rem !important;
    border: none !important;
}

/* Ensure Password Toggle Icon is Not Clipped */
div[data-baseweb="input"] button {
    background-color: transparent !important;
    border: none !important;
    color: #94a3b8 !important;
    padding: 0 8px !important;
    min-width: 32px !important;
}

/* Chat Input Bar Fixes */
div[data-testid="stChatInput"] {
    background-color: #0f172a !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
}

div[data-testid="stChatInput"]:focus-within {
    border-color: #6366f1 !important;
}

/* Custom SaaS Cards */
.saas-card {
    background-color: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 1.15rem;
    margin-bottom: 1rem;
}

.saas-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.65rem;
}

.saas-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: #f8fafc;
    letter-spacing: -0.01em;
}

.saas-subtitle {
    font-size: 0.85rem;
    color: #94a3b8;
    line-height: 1.5;
}

/* Badges */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.725rem;
    font-weight: 500;
    background-color: #1e293b;
    color: #cbd5e1;
    border: 1px solid #334155;
}

.badge-indigo {
    background-color: #1e1b4b;
    color: #a5b4fc;
    border-color: #3730a3;
}

.badge-slate {
    background-color: #1e293b;
    color: #94a3b8;
    border-color: #334155;
}

/* Top Header Bar */
.top-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.5rem 0 0.85rem 0;
    border-bottom: 1px solid #1e293b;
    margin-bottom: 1.25rem;
}

.page-heading {
    font-size: 1.45rem;
    font-weight: 700;
    color: #f8fafc;
    letter-spacing: -0.02em;
    margin: 0;
}

.page-description {
    font-size: 0.85rem;
    color: #94a3b8;
    margin-top: 0.25rem;
    line-height: 1.4;
}

/* Source Citation Cards */
.source-card {
    background-color: #0f172a;
    border: 1px solid #1e293b;
    border-left: 3px solid #6366f1;
    border-radius: 6px;
    padding: 0.75rem 0.9rem;
    margin-top: 0.5rem;
}

.source-title {
    font-size: 0.85rem;
    font-weight: 600;
    color: #e2e8f0;
    margin-bottom: 0.2rem;
}

.source-snippet {
    font-size: 0.8rem;
    color: #94a3b8;
    line-height: 1.45;
}

/* Tab Overrides */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background-color: transparent;
    border-bottom: 1px solid #1e293b;
}

.stTabs [data-baseweb="tab"] {
    background-color: transparent;
    border: none;
    color: #94a3b8;
    font-size: 0.85rem;
    font-weight: 500;
    padding: 0.45rem 0.85rem;
}

.stTabs [aria-selected="true"] {
    color: #818cf8 !important;
    border-bottom: 2px solid #6366f1 !important;
    background-color: transparent !important;
}

/* Hide Streamlit Default Watermarks */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
