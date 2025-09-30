# ------------------- streamlit_app.py -------------------
import streamlit as st
from google import genai
from google.genai import types
from composio import Composio

# ------------------- Setup -------------------
st.set_page_config(page_title="AI Email Agent", layout="centered")
st.title("📧 AI-Powered Email Agent")

# Load API keys from Streamlit secrets
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
COMPOSIO_API_KEY = st.secrets["COMPOSIO_API_KEY"]
AUTH_CONFIG_ID = st.secrets["COMPOSIO_AUTH_CONFIG_ID"]

# Initialize clients
genai_client = genai.Client(api_key=GEMINI_API_KEY)
composio = Composio(api_key=COMPOSIO_API_KEY)

# Store connected account in session
if "connected_account_id" not in st.session_state:
    st.session_state.connected_account_id = None

# ------------------- Gemini AI Function -------------------
def generate_ai_response(user_prompt: str) -> str:
    contents = [
        types.Content(role="user", parts=[types.Part.from_text(text=user_prompt)])
    ]

    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=0),
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_LOW_AND_ABOVE"),
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_LOW_AND_ABOVE"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_LOW_AND_ABOVE"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_LOW_AND_ABOVE"),
        ],
    )

    response_text = ""
    try:
        for chunk in genai_client.models.generate_content_stream(
            model="gemini-2.5-flash",  # fallback handled below
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text:
                response_text += chunk.text
    except Exception as e:
        # Fallback to gemini-1.5-flash
        st.warning("⚠️ Falling back to gemini-1.5-flash")
        response_text = ""
        for chunk in genai_client.models.generate_content_stream(
            model="gemini-1.5-flash",
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text:
                response_text += chunk.text

    return response_text.strip()

# ------------------- Composio Email Function -------------------
def connect_composio_account(user_id: str):
    """Authenticate with Composio and save connected account ID."""
    connection_request = composio.connected_accounts.link(
        user_id, AUTH_CONFIG_ID, callback_url="https://your-app.com/callback"
    )
    st.info(f"👉 Please authenticate your account here: [Authenticate]({connection_request.redirect_url})")

    connected_account = connection_request.wait_for_connection()
    st.session_state.connected_account_id = connected_account.id
    st.success("✅ Account connected successfully!")

def send_email_via_composio(to: str, subject: str, body: str):
    """Send email using Composio Gmail integration."""
    if not st.session_state.connected_account_id:
        st.error("❌ No connected account. Please connect first.")
        return None

    result = composio.actions.execute(
        "gmail.send_email",
        connected_account_id=st.session_state.connected_account_id,
        input={"to": to, "subject": subject, "body": body},
    )
    return result

# ------------------- Streamlit UI -------------------
user_prompt = st.text_area(
    "💬 Ask AI to draft your email:",
    placeholder="e.g., Write a professional email to a client about a meeting..."
)

user_id = "user-1349-129-12"  # Replace with dynamic session/user mapping

if st.button("Generate Email Draft"):
    if user_prompt:
        with st.spinner("🤔 Thinking..."):
            ai_output = generate_ai_response(user_prompt)
        st.subheader("✍️ AI Drafted Email")
        st.write(ai_output)

        with st.form("email_form"):
            to = st.text_input("Recipient Email")
            subject = st.text_input("Subject")
            body = st.text_area("Email Body", value=ai_output)
            send_btn = st.form_submit_button("Send Email")

            if send_btn:
                with st.spinner("📨 Sending via Composio..."):
                    result = send_email_via_composio(to, subject, body)
                    if result:
                        st.success("✅ Email sent successfully!")
                        st.json(result)
    else:
        st.warning("Please enter a prompt first.")

# Option to connect Composio if not already
if not st.session_state.connected_account_id:
    if st.button("🔗 Connect Composio Account"):
        connect_composio_account(user_id)
