import streamlit as st
from google import genai
from google.genai import types
from composio import Composio
from composio_google import GoogleProvider

# ------------------- Setup -------------------
st.set_page_config(page_title="AI Email Agent", layout="centered")
st.title("📧 AI-Powered Email Agent")

# Load secrets
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
COMPOSIO_API_KEY = st.secrets["COMPOSIO_API_KEY"]
AUTH_CONFIG_ID = st.secrets["COMPOSIO_AUTH_CONFIG_ID"]

# ------------------- Initialize Clients -------------------
genai_client = genai.Client(api_key=GEMINI_API_KEY)
composio_client = Composio(api_key=COMPOSIO_API_KEY, provider=GoogleProvider())

# ------------------- Session State -------------------
if "connected_account_id" not in st.session_state:
    st.session_state.connected_account_id = None
if "user_id" not in st.session_state:
    st.session_state.user_id = "user-1"
if "draft" not in st.session_state:
    st.session_state.draft = ""
if "show_form" not in st.session_state:
    st.session_state.show_form = False

# ------------------- Parse Connected Account from URL -------------------
query_params = st.query_params
if "connected_account_id" in query_params and not st.session_state.connected_account_id:
    st.session_state.connected_account_id = query_params["connected_account_id"]
    st.success("✅ Gmail account connected successfully!")

# ------------------- Gemini AI Function -------------------
def generate_ai_response(prompt: str) -> str:
    try:
        contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
        config = types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_budget=0))
        resp = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=config
        )
        return resp.text.strip()
    except Exception as e:
        st.error(f"Gemini API error: {e}")
        return "⚠️ Could not generate AI response."

# ------------------- Composio Gmail Functions -------------------
def connect_composio_account(user_id: str):
    try:
        conn_req = composio_client.connected_accounts.link(
            user_id=user_id,
            auth_config_id=AUTH_CONFIG_ID,
            callback_url="https://evercreate.streamlit.app/"
        )
        st.info(f"Authenticate here: [Link]({conn_req.redirect_url})")
    except Exception as e:
        st.error(f"Connection error: {e}")

def send_email(to: str, subject: str, body: str):
    if not st.session_state.connected_account_id:
        st.error("Connect Gmail account first!")
        return None

    try:
        result = composio_client.connected_accounts.run_action(
            connected_account_id=st.session_state.connected_account_id,
            action="composio_google__gmail_send_email",
            params={
                "to": to,
                "subject": subject,
                "body": body
            }
        )
        return result
    except Exception as e:
        st.error(f"Error sending email: {e}")
        return None

# ------------------- Streamlit UI -------------------
st.subheader("💬 Draft Email (Optional AI)")
user_prompt = st.text_area("Ask AI to draft your email:", placeholder="Write something for AI to draft...")

if st.button("Generate Draft"):
    if user_prompt.strip() == "":
        st.warning("Please enter a prompt for AI.")
    else:
        with st.spinner("Generating draft…"):
            st.session_state.draft = generate_ai_response(user_prompt)
            st.session_state.show_form = True

if st.session_state.show_form or st.session_state.connected_account_id:
    st.subheader("📝 Draft / Compose Email")
    to = st.text_input("To (recipient email)")
    subject = st.text_input("Subject")
    body = st.text_area("Body", value=st.session_state.draft, height=200)

    if st.button("Send Email"):
        if not to.strip() or not subject.strip() or not body.strip():
            st.error("Please fill all fields!")
        else:
            with st.spinner("Sending email…"):
                resp = send_email(to, subject, body)
                if resp:
                    st.success("✅ Email sent successfully!")
                    st.json(resp)
                    st.session_state.draft = ""
                    st.session_state.show_form = False
                else:
                    st.error("❌ Failed to send email")

# ------------------- Connection -------------------
st.divider()
if not st.session_state.connected_account_id:
    if st.button("🔗 Connect Google Account"):
        connect_composio_account(st.session_state.user_id)
else:
    st.success("✅ Google Account Connected")
    if st.button("🔌 Disconnect"):
        st.session_state.connected_account_id = None
        st.experimental_rerun()
