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

# Session state
if "connected_account_id" not in st.session_state:
    st.session_state.connected_account_id = None

# ------------------- Gemini AI Function -------------------

def generate_ai_response(prompt: str) -> str:
    contents = [ types.Content(role="user", parts=[types.Part.from_text(text=prompt)]) ]
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
        # Fallback
        try:
            resp2 = genai_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=config,
            )
            return resp2.text.strip()
        except Exception as e2:
            st.error(f"Fallback Gemini error: {e2}")
            return "⚠️ Could not generate AI response."

# ------------------- Composio Email Functions -------------------

def connect_composio_account(user_id: str):
    conn_req = composio.connected_accounts.link(
        user_id, AUTH_CONFIG_ID, callback_url="https://evercreate.streamlit.app/"
    )
    st.info(f"Authenticate here: [Link]({conn_req.redirect_url})")
    connected = conn_req.wait_for_connection()
    st.session_state.connected_account_id = connected.id
    st.success("✅ Gmail account connected")

def send_email(to: str, subject: str, body: str):
    if not st.session_state.connected_account_id:
        st.error("No connected Gmail account — click Connect Google Account first.")
        return None

    # Use Composio Gmail tool “GMAIL_SEND_EMAIL”
    result = composio.actions.execute(
        "gmail.send_email",
        connected_account_id=st.session_state.connected_account_id,
        input={
            "recipient_email": to,
            "subject": subject,
            "body": body,
            "is_html": False
        },
    )
    return result

# ------------------- Streamlit UI -------------------

user_prompt = st.text_area("💬 Ask AI to draft your email:", placeholder="Write an email to a client...")
user_id = "user-1"  # Ideally tied to real user

if st.button("Generate Email Draft"):
    if user_prompt.strip() == "":
        st.warning("Please enter a prompt.")
    else:
        with st.spinner("Generating..."):
            draft = generate_ai_response(user_prompt)
        st.subheader("📝 Draft")
        st.write(draft)

        with st.form("email_form"):
            to = st.text_input("To (recipient email)")
            subject = st.text_input("Subject")
            body = st.text_area("Body", value=draft)
            btn = st.form_submit_button("Send Email")
            if btn:
                with st.spinner("Sending email…"):
                    resp = send_email(to, subject, body)
                    if resp:
                        st.success("✅ Email sent")
                        st.json(resp)
                    else:
                        st.error("❌ Failed to send email")

if not st.session_state.connected_account_id:
    if st.button("🔗 Connect Google Account"):
        connect_composio_account(user_id)
