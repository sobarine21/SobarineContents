# streamlit_app.py

import streamlit as st
from google import genai
from google.genai import types
from composio import Composio

# ------------------- Setup -------------------
st.set_page_config(page_title="AI Email Agent", layout="centered")
st.title("📧 AI-Powered Email Agent")

# Load secrets
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
COMPOSIO_API_KEY = st.secrets["COMPOSIO_API_KEY"]
AUTH_CONFIG_ID = st.secrets["COMPOSIO_AUTH_CONFIG_ID"]

# Initialize clients
genai_client = genai.Client(api_key=GEMINI_API_KEY)
composio = Composio(api_key=COMPOSIO_API_KEY)

# Session state initialization
if "connected_account_id" not in st.session_state:
    st.session_state.connected_account_id = None
if "draft" not in st.session_state:
    st.session_state.draft = ""
if "show_form" not in st.session_state:
    st.session_state.show_form = False

# ------------------- Gemini AI Function -------------------

def generate_ai_response(prompt: str) -> str:
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
    config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=0),
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_LOW_AND_ABOVE"),
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_LOW_AND_ABOVE"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_LOW_AND_ABOVE"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_LOW_AND_ABOVE"),
        ],
    )
    try:
        resp = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=config,
        )
        return resp.text.strip()
    except Exception as e:
        st.error(f"Gemini API error: {e}")
        return "⚠️ Could not generate AI response."

# ------------------- Composio Email Functions -------------------

def connect_composio_account(user_id: str):
    conn_req = composio.connected_accounts.link(
        user_id=user_id,
        auth_config_id=AUTH_CONFIG_ID,
        callback_url="https://evercreate.streamlit.app/"
    )
    st.info(f"Authenticate here: [Link]({conn_req.redirect_url})")
    connected = conn_req.wait_for_connection()
    st.session_state.connected_account_id = connected.id
    st.success("✅ Gmail account connected")

def send_email(to: str, subject: str, body: str):
    if not st.session_state.connected_account_id:
        st.error("No connected Gmail account — click Connect Google Account first.")
        return None

    try:
        result = composio.actions.execute_action(
            action="gmail.send_email",
            connected_account_id=st.session_state.connected_account_id,
            params={
                "to": to,
                "subject": subject,
                "body": body,
                "is_html": False
            },
        )
        return result
    except Exception as e:
        st.error(f"Composio send_email error: {e}")
        return None

# ------------------- Streamlit UI -------------------

user_prompt = st.text_area("💬 Ask AI to draft your email:", placeholder="Write an email to a client...")
user_id = "user-1"  # Replace with real user in production

if st.button("Generate Email Draft"):
    if user_prompt.strip() == "":
        st.warning("Please enter a prompt.")
    else:
        with st.spinner("Generating..."):
            draft = generate_ai_response(user_prompt)
        st.session_state.draft = draft
        st.session_state.show_form = True

# Show draft and form if available
if st.session_state.show_form and st.session_state.draft:
    st.subheader("📝 Draft")
    st.write(st.session_state.draft)

    with st.form("email_form"):
        to = st.text_input("To (recipient email)")
        subject = st.text_input("Subject")
        body = st.text_area("Body", value=st.session_state.draft, height=200)
        btn = st.form_submit_button("Send Email")
        
        if btn:
            if not to.strip() or not subject.strip():
                st.error("Please fill in both 'To' and 'Subject' fields.")
            else:
                with st.spinner("Sending email…"):
                    resp = send_email(to, subject, body)
                    if resp:
                        st.success("✅ Email sent successfully!")
                        st.json(resp)
                        # Clear the draft after successful send
                        st.session_state.draft = ""
                        st.session_state.show_form = False
                    else:
                        st.error("❌ Failed to send email")

# Connection button at the bottom
st.divider()
if not st.session_state.connected_account_id:
    if st.button("🔗 Connect Google Account"):
        connect_composio_account(user_id)
else:
    st.success("✅ Google Account Connected")
    if st.button("🔌 Disconnect"):
        st.session_state.connected_account_id = None
        st.rerun()
