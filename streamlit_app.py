# streamlit_app.py

import streamlit as st
from google import genai
from google.genai import types
from composio import Composio
import base64
from email.mime.text import MIMEText

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

# Session state for connected account
if "connected_account_id" not in st.session_state:
    st.session_state.connected_account_id = None

# ------------------- Gemini AI Function -------------------

def generate_ai_response(user_prompt: str) -> str:
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=user_prompt)])]

    gen_config = types.GenerateContentConfig(
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
            config=gen_config,
        )
        return resp.text.strip()
    except Exception as e:
        st.error(f"Gemini error: {e}")
        return "❌ Error generating response."

# ------------------- Composio Email Functions -------------------

def connect_composio_account(user_id: str):
    """Initiate Composio OAuth flow and store connected_account_id."""
    connection_request = composio.connected_accounts.link(
        user_id, AUTH_CONFIG_ID, callback_url="https://your-app.com/callback"
    )
    st.info(f"Authenticate your account: [Click here]({connection_request.redirect_url})")

    connected_account = connection_request.wait_for_connection()
    st.session_state.connected_account_id = connected_account.id
    st.success("✅ Account connected!")

def create_message(to: str, subject: str, body: str) -> str:
    """Create RFC822 base64-encoded email for Gmail API."""
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    return raw_message

def send_email_via_composio(to: str, subject: str, body: str):
    if not st.session_state.connected_account_id:
        st.error("No connected account. Please connect first.")
        return None

    raw_message = create_message(to, subject, body)

    result = composio.actions.execute(
        "gmail.users.messages.send",   # ✅ Correct Gmail action
        connected_account_id=st.session_state.connected_account_id,
        input={"userId": "me", "message": {"raw": raw_message}},
    )
    return result

# ------------------- Streamlit UI -------------------

user_prompt = st.text_area(
    "💬 Ask AI to draft your email:",
    placeholder="e.g. Write a professional email to a client about a meeting..."
)
user_id = "user-unique-id-1"  # Replace per actual user logic

if st.button("Generate Draft"):
    if user_prompt.strip() == "":
        st.warning("Enter some prompt first.")
    else:
        with st.spinner("Generating via Gemini..."):
            ai_output = generate_ai_response(user_prompt)
        st.subheader("✍️ Drafted Email")
        st.write(ai_output)

        with st.form("send_email_form"):
            to = st.text_input("To (recipient email)")
            subject = st.text_input("Subject")
            body = st.text_area("Body", value=ai_output)
            send_btn = st.form_submit_button("Send Email")
            if send_btn:
                with st.spinner("Sending email..."):
                    res = send_email_via_composio(to, subject, body)
                    if res:
                        st.success("✅ Email sent!")
                        st.json(res)

if not st.session_state.connected_account_id:
    if st.button("🔗 Connect Google Account"):
        connect_composio_account(user_id)
