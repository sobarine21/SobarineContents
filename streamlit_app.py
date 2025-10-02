import streamlit as st
from google import genai
from google.genai import types
from composio import Composio

# --- Page Setup ---
st.set_page_config(page_title="AI Email Agent", layout="centered", page_icon="📧")
st.title("📧 AI-Powered Email Agent")

# --- Load Credentials & Initialize Clients ---
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    COMPOSIO_API_KEY = st.secrets["COMPOSIO_API_KEY"] 
    AUTH_CONFIG_ID = st.secrets["COMPOSIO_AUTH_CONFIG_ID"]
    
    genai.configure(api_key=GEMINI_API_KEY)
    composio_client = Composio(api_key=COMPOSIO_API_KEY)
except KeyError as e:
    st.error(f"Missing secret: {e}. Please add it to your Streamlit secrets.")
    st.stop()
except Exception as e:
    st.error(f"Failed to initialize clients: {e}")
    st.stop()

# --- Initialize Session State ---
for key, default_value in [
    ("connected_account_id", None),
    ("user_id", "user-1"), 
    ("draft", ""),
    ("show_form", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default_value

# --- Handle Connection Callback ---
query_params = st.query_params
if "connected_account_id" in query_params and not st.session_state.connected_account_id:
    st.session_state.connected_account_id = query_params["connected_account_id"]
    st.success("✅ Gmail account connected successfully!")
    st.query_params.clear()

# --- Core Functions ---
def generate_ai_response(prompt: str) -> str:
    """Generates an email draft using the Gemini API."""
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"Gemini API Error: {e}")
        return "⚠️ Could not generate AI response."

def connect_composio_account(user_id: str):
    """Initiates the Composio connection flow."""
    try:
        conn_req = composio_client.connected_accounts.link(
            user_id=user_id,
            auth_config_id=AUTH_CONFIG_ID,
            callback_url="https://your-app.streamlit.app/",  # Update this
        )
        st.link_button("🔗 Authenticate with Google", conn_req.redirect_url)
    except Exception as e:
        st.error(f"Connection Error: {e}")

def send_email(to: str, subject: str, body: str):
    """Sends an email using the Composio API."""
    if not st.session_state.connected_account_id:
        st.error("Connect your Gmail account first!")
        return None
    try:
        response = composio_client.tools.invoke(
            user_id=st.session_state.user_id,
            tool_id="GMAIL_SEND_MESSAGE",
            params={
                "to": to,
                "subject": subject,
                "message": body
            }
        )
        return response
    except Exception as e:
        st.error(f"Error sending email: {e}")
        return None

# --- UI: Gmail Connection ---
if not st.session_state.connected_account_id:
    st.warning("⚠️ Please connect your Gmail account to send emails")
    connect_composio_account(st.session_state.user_id)
    st.divider()

# --- UI: AI Draft Generation ---
with st.expander("💬 Draft an Email with AI", expanded=True):
    user_prompt = st.text_area("Your prompt:", placeholder="e.g., Write a follow-up email...")
    if st.button("Generate Draft", key="generate"):
        if not user_prompt.strip():
            st.warning("Please enter a prompt for the AI.")
        else:
            with st.spinner("🤖 AI is drafting your email..."):
                st.session_state.draft = generate_ai_response(user_prompt)
                st.session_state.show_form = True

# --- UI: Email Composition and Sending Form ---
if st.session_state.show_form or st.session_state.connected_account_id:
    st.subheader("📝 Compose and Send")
    with st.form("email_form"):
        to = st.text_input("To (Recipient Email)")
        subject = st.text_input("Subject")
        body = st.text_area("Message Body", value=st.session_state.draft, height=200)
        
        submit = st.form_submit_button("Send Email")
        if submit:
            if not all([to, subject, body]):
                st.error("Please fill in all fields!")
            else:
                with st.spinner("Sending email..."):
                    response = send_email(to, subject, body)
                    if response:
                        st.success("✅ Email sent successfully!")
                        st.session_state.draft = ""
                        st.session_state.show_form = False
