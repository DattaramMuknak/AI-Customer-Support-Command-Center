import os

import httpx
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


def api_request(method: str, path: str, token: str | None = None, json: dict | list | None = None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.request(method, f"{API_BASE_URL}{path}", headers=headers, json=json)
        if response.status_code >= 400:
            detail = response.json().get("detail", response.text)
            st.error(f"{response.status_code}: {detail}")
            return None
        return response.json()
    except httpx.HTTPError as exc:
        st.error(f"API connection failed: {exc}")
        return None


st.set_page_config(page_title="AI Support Platform", page_icon="AI", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --ink: #172033;
        --muted: #64748b;
        --line: #e2e8f0;
        --blue: #2563eb;
        --navy: #14213d;
        --surface: #ffffff;
        --background: #f5f7fb;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: var(--background);
        color: var(--ink);
    }

    .block-container {
        max-width: 1320px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #14213d;
        border-right: 1px solid #263653;
    }

    section[data-testid="stSidebar"] * {
        color: #f1f5f9;
    }

    section[data-testid="stSidebar"] textarea,
    section[data-testid="stSidebar"] input {
        background: #1d2d4a;
        border: 1px solid #3b4b66;
        border-radius: 8px;
        color: #ffffff;
    }

    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
        font-size: 1.05rem;
        font-weight: 700;
    }

    /* Main header */
    .hero {
        padding: 30px 32px;
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 14px;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.035);
    }

    .hero h1 {
        margin: 0 0 10px;
        color: #14213d;
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: -0.8px;
        line-height: 1.25;
    }

    .hero p {
        margin: 0;
        max-width: 800px;
        color: var(--muted);
        font-size: 0.95rem;
        line-height: 1.7;
    }

    /* Header information cards */
    .hero-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 14px;
        margin-top: 25px;
    }

    .metric-card {
        padding: 16px 18px;
        background: #f8fafc;
        border: 1px solid var(--line);
        border-radius: 10px;
        min-width: 0;
    }

    .metric-card span {
        display: block;
        margin-bottom: 7px;
        color: #64748b;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.7px;
        text-transform: uppercase;
    }

    .metric-card strong {
        display: block;
        color: #172033;
        font-size: 0.92rem;
        font-weight: 700;
        overflow-wrap: anywhere;
    }

    /* Content cards */
    .section-card {
        margin-bottom: 18px;
        padding: 24px;
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 12px;
        box-shadow: 0 3px 12px rgba(15, 23, 42, 0.025);
    }

    .section-card h3 {
        margin: 0 0 8px;
        color: #14213d;
        font-size: 1.08rem;
        font-weight: 700;
        letter-spacing: -0.2px;
    }

    .section-card p {
        margin: 0 0 18px;
        color: var(--muted);
        font-size: 0.88rem;
        line-height: 1.6;
    }

    /* Tabs */
    div[data-testid="stTabs"] {
        margin-top: 22px;
    }

    div[data-testid="stTabs"] [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid var(--line);
    }

    div[data-testid="stTabs"] button[data-baseweb="tab"] {
        padding: 12px 17px;
        color: #64748b;
        font-size: 0.88rem;
        font-weight: 600;
    }

    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: var(--blue);
    }

    div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
        background: var(--blue);
    }

    /* Buttons */
    .stButton > button,
    .stFormSubmitButton > button {
        min-height: 42px;
        padding: 9px 17px;
        color: #ffffff;
        background: var(--blue);
        border: 1px solid var(--blue);
        border-radius: 8px;
        font-size: 0.87rem;
        font-weight: 600;
        box-shadow: none;
        transition: background 0.15s ease, border-color 0.15s ease;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        color: #ffffff;
        background: #1d4ed8;
        border-color: #1d4ed8;
    }

    .stButton > button:focus-visible,
    .stFormSubmitButton > button:focus-visible {
        outline: 2px solid #93c5fd;
        outline-offset: 2px;
    }

    /* Inputs */
    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox [data-baseweb="select"] > div {
        border: 1px solid #d7dfeb;
        border-radius: 8px;
        background: #ffffff;
    }

    .stTextInput input,
    .stTextArea textarea {
        color: #172033;
    }

    .stTextInput input:focus,
    .stTextArea textarea:focus {
        border-color: var(--blue);
        box-shadow: 0 0 0 1px var(--blue);
    }

    label,
    [data-testid="stWidgetLabel"] p {
        color: #334155;
        font-size: 0.86rem;
        font-weight: 600;
    }

    /* AI response */
    .agent-response {
        padding: 18px 20px;
        margin: 12px 0;
        color: #164e40;
        background: #f0fdf7;
        border: 1px solid #bbf7d0;
        border-left: 4px solid #10b981;
        border-radius: 8px;
        font-size: 0.93rem;
        line-height: 1.75;
        overflow-wrap: anywhere;
    }

    /* Session status */
    .status-pill {
        display: inline-flex;
        align-items: center;
        padding: 7px 11px;
        color: #a7f3d0;
        background: rgba(16, 185, 129, 0.13);
        border: 1px solid rgba(110, 231, 183, 0.22);
        border-radius: 7px;
        font-size: 0.78rem;
        font-weight: 600;
    }

    /* Data tables */
    div[data-testid="stDataFrame"] {
        border: 1px solid var(--line);
        border-radius: 9px;
        overflow: hidden;
    }

    /* Alerts */
    div[data-testid="stAlert"] {
        border-radius: 9px;
    }

    /* Responsive layout */
    @media (max-width: 760px) {
        .block-container {
            padding: 1rem 1rem 2rem;
        }

        .hero {
            padding: 22px 20px;
        }

        .hero h1 {
            font-size: 1.55rem;
            letter-spacing: -0.4px;
        }

        .hero-grid {
            grid-template-columns: 1fr;
            gap: 10px;
        }

        .section-card {
            padding: 18px;
        }

        div[data-testid="stTabs"] button[data-baseweb="tab"] {
            padding: 10px 8px;
            font-size: 0.8rem;
        }
    }
</style>

    """,
    unsafe_allow_html=True,
)

if "token" not in st.session_state:
    st.session_state.token = ""
if "ticket_id" not in st.session_state:
    st.session_state.ticket_id = ""

token_status = "Authenticated" if st.session_state.token else "Guest session"
ticket_status = st.session_state.ticket_id or "No active ticket"

st.markdown(
    f"""
    <div class="hero">
        <h1>AI Customer Support Command Center</h1>
        <p>Operate the support workflow from one place: authenticate, create tickets, run the agent graph, and ingest knowledge documents into the RAG store.</p>
        <div class="hero-grid">
            <div class="metric-card"><span>Backend</span><strong>{API_BASE_URL}</strong></div>
            <div class="metric-card"><span>Session</span><strong>{token_status}</strong></div>
            <div class="metric-card"><span>Active Ticket</span><strong>{ticket_status}</strong></div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("")

with st.sidebar:
    st.markdown("### Control Panel")
    st.markdown(f'<div class="status-pill">{token_status}</div>', unsafe_allow_html=True)
    st.write("")
    token_input = st.text_area("JWT token", value=st.session_state.token, height=120)
    if token_input != st.session_state.token:
        st.session_state.token = token_input.strip()

    if st.button("Clear session"):
        st.session_state.token = ""
        st.session_state.ticket_id = ""
        st.rerun()


auth_tab, ticket_tab, chat_tab, kb_tab = st.tabs(["Access", "Tickets", "Agent Chat", "Knowledge Base"])

with auth_tab:
    register_col, login_col = st.columns(2)

    
    with register_col:
        st.markdown(
            '<div class="section-card"><h3>Create Account</h3>'
            '<p>Register to access the AI customer support platform.</p>',
            unsafe_allow_html=True,
        )

        with st.form("register_form"):
            email = st.text_input("Email", key="register_email")
            full_name = st.text_input("Full name", key="register_full_name")
            password = st.text_input(
                "Password", type="password", key="register_password"
            )

            role = st.selectbox(
                "Select account role",
                ["Normal User", "Admin"],
                key="register_role",
            )

            st.caption(
                "Normal users can use support features. "
                "Admins can access protected knowledge-base features."
            )

            submitted = st.form_submit_button(
                "Create account", use_container_width=True
            )

        if submitted:
            if not email.strip() or not full_name.strip() or not password:
                st.warning("Please fill in all fields.")
            else:
                result = api_request(
                    "POST",
                    "/api/v1/auth/register",
                    json={
                        "email": email.strip(),
                        "full_name": full_name.strip(),
                        "password": password,
                        "is_admin": role == "Admin",
                    },
                )

                if result:
                    st.success(
                        f"{role} account created successfully!"
                    )
                    st.json(result)

        st.markdown("</div>", unsafe_allow_html=True)

    with login_col:
        st.markdown('<div class="section-card"><h3>Secure Login</h3><p>Sign in and load the JWT token into this frontend session.</p>', unsafe_allow_html=True)
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login")
        if submitted:
            result = api_request("POST", "/api/v1/auth/login", json={"email": email, "password": password})
            if result:
                st.session_state.token = result["access_token"]
                st.success("Logged in")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

with ticket_tab:
    create_col, list_col = st.columns([0.9, 1.1])
    with create_col:
        st.markdown('<div class="section-card"><h3>Create Ticket</h3><p>Start a support case and attach the first customer message.</p>', unsafe_allow_html=True)
        with st.form("ticket_form"):
            subject = st.text_input("Subject", value="Refund policy")
            initial_message = st.text_area("Initial message", value="I want to know the refund policy.")
            submitted = st.form_submit_button("Create ticket")
        if submitted:
            result = api_request(
                "POST",
                "/api/v1/tickets",
                token=st.session_state.token,
                json={"subject": subject, "initial_message": initial_message},
            )
            if result:
                st.session_state.ticket_id = result["id"]
                st.success("Ticket created")
                st.json(result)
        st.markdown("</div>", unsafe_allow_html=True)

    with list_col:
        st.markdown('<div class="section-card"><h3>Ticket Queue</h3><p>Review tickets created by the active user.</p>', unsafe_allow_html=True)
        if st.button("Load tickets"):
            result = api_request("GET", "/api/v1/tickets", token=st.session_state.token)
            if result is not None:
                st.dataframe(result, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

with chat_tab:
    st.markdown('<div class="section-card"><h3>Agent Chat Console</h3><p>Send a message through the LangGraph support pipeline.</p>', unsafe_allow_html=True)
    ticket_id = st.text_input("Ticket ID", value=st.session_state.ticket_id)
    message = st.text_area("Message", value="Can you summarize the refund policy?")
    if st.button("Send message"):
        result = api_request(
            "POST",
            "/api/v1/chat",
            token=st.session_state.token,
            json={"ticket_id": ticket_id, "message": message},
        )
        if result:
            st.success("Agent response")
            st.markdown(f'<div class="agent-response">{result["response"]}</div>', unsafe_allow_html=True)
            st.json(result)
    st.markdown("</div>", unsafe_allow_html=True)

with kb_tab:
    st.markdown('<div class="section-card"><h3>Knowledge Base Ingestion</h3><p>Push policy or support content into the RAG vector store. Admin token required.</p>', unsafe_allow_html=True)
    st.warning("This endpoint requires an admin token.")
    with st.form("kb_form"):
        title = st.text_input("Title", value="Refund Policy")
        category = st.text_input("Category", value="billing")
        content = st.text_area("Content", value="Customers can request a refund within 30 days of purchase.")
        source = st.text_input("Metadata source", value="streamlit")
        submitted = st.form_submit_button("Ingest document")
    if submitted:
        result = api_request(
            "POST",
            "/api/v1/knowledge-base/ingest",
            token=st.session_state.token,
            json={
                "title": title,
                "content": content,
                "category": category,
                "metadata": {"source": source},
            },
        )
        if result:
            st.success("Document ingested")
            st.json(result)
    st.markdown("</div>", unsafe_allow_html=True)
