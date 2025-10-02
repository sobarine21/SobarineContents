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
    
    genai_client = genai.Client(api_key=GEMINI_API_KEY)
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
        contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
        config = types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_budget=0))
        resp = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=config,
        )
        return resp.text.strip()
    except Exception as e:
        st.error(f"Gemini API Error: {e}")
        return "⚠️ Could not generate AI response."

def connect_composio_account(user_id: str):
    """Initiates the Composio connection flow."""
    try:
        conn_req = composio_client.connected_accounts.link(
            user_id=user_id,
            auth_config_id=AUTH_CONFIG_ID,
            callback_url="https://evercreate.streamlit.app/",
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
        # Assuming the correct method to send an email is 'send_email'
        response = composio_client.tools.send_email(
            user_id=st.session_state.user_id,
            params={
                "to": to,
                "subject": subject,
                "body": body
            }
        )
        return response
    except Exception as e:
        st.error(f"Error sending email: {e}")
        return None

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
        body = st.text_area("Body", value=st.session_state.draft, height=250)
        
        submitted = st.form_submit_button("Send Email")
        if submitted:
            if not all([to.strip(), subject.strip(), body.strip()]):
                st.error("Please fill in all fields to send the email.")
            else:
                with st.spinner("Sending email..."):
                    resp = send_email(to, subject, body)
                    if resp and resp.get("execution_details", {}).get("success"):
                        st.success("✅ Email sent successfully!")
                        st.json(resp.get("response_data", {}))
                        st.session_state.draft = ""
                        st.session_state.show_form = False
                    else:
                        st.error(f"❌ Failed to send email. Error: {resp.get('error') if resp else 'Unknown'}")

# --- UI: Connection Management ---
st.divider()
if not st.session_state.connected_account_id:
    st.subheader("Connect Your Account")
    connect_composio_account(st.session_state.user_id)
else:
    st.success("✅ Google Account is Connected.")
    if st.button("🔌 Disconnect Account"):
        st.session_state.connected_account_id = None
        st.rerun()
