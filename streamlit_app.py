import streamlit as st
from google import genai
from google.genai import types
from composio import Composio
from composio_google import GoogleProvider  # ensure this matches your import

# ------------------- Setup -------------------
st.set_page_config(page_title="AI Email Agent", layout="centered")
st.title("📧 AI-Powered Email Agent")

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
COMPOSIO_API_KEY = st.secrets["COMPOSIO_API_KEY"]
AUTH_CONFIG_ID = st.secrets["COMPOSIO_AUTH_CONFIG_ID"]

# Initialize clients
genai_client = genai.Client(api_key=GEMINI_API_KEY)
# Use GoogleProvider explicitly
composio_client = Composio[GoogleProvider](api_key=COMPOSIO_API_KEY)

# Session state defaults
if "connected_account_id" not in st.session_state:
    st.session_state.connected_account_id = None
if "user_id" not in st.session_state:
    st.session_state.user_id = "user-1"
if "draft" not in st.session_state:
    st.session_state.draft = ""
if "show_form" not in st.session_state:
    st.session_state.show_form = False

# ------------------- Gemini AI Function -------------------
def generate_ai_response(prompt: str) -> str:
    contents = [
        types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
    ]
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
    try:
        conn_req = composio_client.connected_accounts.link(
            user_id=user_id,
            auth_config_id=AUTH_CONFIG_ID,
            callback_url="https://your-callback-url"
        )
        st.info(f"Authenticate here: [Link]({conn_req.redirect_url})")
        connected = conn_req.wait_for_connection()
        st.session_state.connected_account_id = connected.id
        st.session_state.user_id = user_id
        st.success("✅ Gmail account connected")
    except Exception as e:
        st.error(f"Connection error: {e}")

def send_email_with_composio(to: str, subject: str, body: str):
    if not st.session_state.user_id:
        st.error("No user ID found.")
        return None

    try:
        # Prompt for the AI / tool calling
        prompt = (
            f"You are an assistant that can send emails using the GMAIL_SEND_EMAIL tool.\n"
            f"Use the following parameters:\n"
            f"to: {to}\n"
            f"subject: {subject}\n"
            f"body: {body}\n\n"
            f"Invoke the tool appropriately."
        )

        # Get the tool definition from composio for this user
        tools = composio_client.tools.get(
            user_id=st.session_state.user_id,
            tools=["GMAIL_SEND_EMAIL"]
        )

        # Call Gemini with tool context
        contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_LOW_AND_ABOVE"),
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_LOW_AND_ABOVE"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_LOW_AND_ABOVE"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_LOW_AND_ABOVE"),
            ],
            # **Here** attach the tools so Gemini can output tool calls
            tools=tools
        )

        resp = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=config
        )

        # At this point, `resp` is the rich response object with .choices etc.
        # Pass **that** into composio.handle_tool_calls
        result = composio_client.provider.handle_tool_calls(
            response=resp,
            user_id=st.session_state.user_id
        )

        return result

    except Exception as e:
        st.error(f"Error sending email: {e}")
        import traceback
        st.error(traceback.format_exc())
        return None

# ------------------- Streamlit UI -------------------
user_prompt = st.text_area("💬 Ask AI to draft your email:", placeholder="Write an email to a client...")

if st.button("Generate Email Draft"):
    if user_prompt.strip() == "":
        st.warning("Please enter a prompt.")
    else:
        with st.spinner("Generating..."):
            draft = generate_ai_response(user_prompt)
        st.session_state.draft = draft
        st.session_state.show_form = True

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
                    resp = send_email_with_composio(to, subject, body)
                    if resp:
                        st.success("✅ Email sent successfully!")
                        st.json(resp)
                        st.session_state.draft = ""
                        st.session_state.show_form = False
                    else:
                        st.error("❌ Failed to send email")

st.divider()
if not st.session_state.connected_account_id:
    if st.button("🔗 Connect Google Account"):
        connect_composio_account(st.session_state.user_id)
else:
    st.success("✅ Google Account Connected")
    if st.button("🔌 Disconnect"):
        st.session_state.connected_account_id = None
        st.experimental_rerun()
