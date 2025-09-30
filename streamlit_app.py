# ------------------- streamlit_app.py -------------------
import streamlit as st
import os
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

# ------------------- Gemini AI Function -------------------
def generate_ai_response(user_prompt: str) -> str:
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_prompt)],
        )
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
    for chunk in genai_client.models.generate_content_stream(
        model="gemini-2.5-flash",
        contents=contents,
        config=generate_content_config,
    ):
        response_text += chunk.text
    return response_text.strip()

# ------------------- Composio Email Function -------------------
def send_email_via_composio(user_id: str, to: str, subject: str, body: str):
    # Step 1: Link account (redirect to Google OAuth via Composio)
    connection_request = composio.connected_accounts.link(
        user_id, AUTH_CONFIG_ID, callback_url="https://your-app.com/callback"
    )

    st.info(f"Authenticate your account here: [Click to Authenticate]({connection_request.redirect_url})")

    # Step 2: Wait until connection is established
    connected_account = connection_request.wait_for_connection()

    # Step 3: Use Composio to send email
    result = composio.actions.execute(
        "gmail.send_email",
        connected_account_id=connected_account.id,
        input={
            "to": to,
            "subject": subject,
            "body": body
        },
    )
    return result

# ------------------- Streamlit UI -------------------
user_prompt = st.text_area("💬 Ask AI to draft your email:", placeholder="e.g., Write a professional email to a client about a meeting...")
user_id = "user-1349-129-12"  # You could also tie this to st.session_state

if st.button("Generate Email Draft"):
    if user_prompt:
        ai_output = generate_ai_response(user_prompt)
        st.subheader("✍️ AI Drafted Email")
        st.write(ai_output)

        with st.form("email_form"):
            to = st.text_input("Recipient Email")
            subject = st.text_input("Subject")
            body = st.text_area("Email Body", value=ai_output)
            send_btn = st.form_submit_button("Send Email")

            if send_btn:
                with st.spinner("Sending via Composio..."):
                    result = send_email_via_composio(user_id, to, subject, body)
                    st.success("✅ Email sent successfully!")
                    st.json(result)
    else:
        st.warning("Please enter a prompt first.")
