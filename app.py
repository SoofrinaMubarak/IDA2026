import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo
from openai import OpenAI
import gspread
from google.oauth2.service_account import Credentials

# 1. Premium & Accessible Page Configuration
st.set_page_config(page_title="IDA Presentation AI Assistant", page_icon="🤖", layout="centered")

# Custom Branding CSS (Dyslexia-friendly spacing, high contrast, clean presentation layout)
st.markdown("""
    <style>
    .main-container {
        background-color: #FDFBF7; /* Off-white/Cream for visual comfort */
        padding: 20px;
        border-radius: 10px;
    }
    .main-title {
        font-size: 36px !important;
        font-weight: 800;
        color: #0F172A; /* Deep Navy text */
        text-align: center;
        margin-top: 10px;
        margin-bottom: 2px;
    }
    .presenters {
        font-size: 16px !important;
        color: #0284C7; /* Professional Sky Blue */
        text-align: center;
        font-weight: 600;
        margin-bottom: 5px;
    }
    .subtitle {
        font-size: 16px !important;
        color: #475569; /* Slate Gray */
        text-align: center;
        margin-bottom: 25px;
    }
    .stChatMessage {
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        line-height: 1.6;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Render Official DAS Logo Asset & Presenter Headings
# Fixed: Pointing to a direct valid image file delivery address
st.image("https://das.org.sg", width=220, use_container_width=False)

st.markdown('<div class="main-title">IDA Presentation AI Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="presenters">Presented by: Dr Geetha Shantha Ram & Ms Soofrina Mubarak</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Dyslexia Association of Singapore (DAS) — Live Presentation Q&A Hub</div>', unsafe_allow_html=True)
st.divider()

# 3. Secure Credentials Loader
try:
    api_key = st.secrets["OPENAI_API_KEY"]
    gs_credentials = st.secrets["gspread_credentials"]
except KeyError:
    st.error("⚠️ Configuration Setup Error: Missing required API keys in the dashboard secrets vault.")
    st.stop()

# Initialize AI & Data Connections
client = OpenAI(api_key=api_key)

def log_to_google_sheet(question, answer):
    """Securely appends live presentation interactions to the shared log sheet."""
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(dict(gs_credentials), scopes=scopes)
        gs_client = gspread.authorize(creds)
        
        # Opens the presentation log sheet by its ID (from the sheet's URL)
        sheet = gs_client.open_by_key("1xd6R6Vc6yhjKw89s-Ol5o-Uo5QmjXDqJNHZfkwBrsCc").sheet1
        timestamp = datetime.now(ZoneInfo("Asia/Singapore")).strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([timestamp, question, answer])
    except Exception as e:
        # Never crash the chat, but record the reason in the Streamlit logs
        print(f"Google Sheet logging failed: {e!r}")

# 4. Persistent Conversation Management
if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_id" not in st.session_state:
    conversation = client.conversations.create()
    st.session_state.conversation_id = conversation.id

SYSTEM_INSTRUCTIONS = """
You are an expert Subject Matter Expert chatbot for the Dyslexia Association of Singapore presentation. 
Answer user questions accurately based on the slides. Keep your answers brief and limited to a maximum of 3 sentences 
so they are easy to read on mobile phones and presentation monitors. 
If you don't know the answer based on the knowledge base, politely state that you do not know.
"""

# 5. Display Active Chat Stream
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. Live Audience Processing Hub
if user_query := st.chat_input("Type your question here for Dr Geetha & Ms Soofrina's AI..."):
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        
        try:
            response = client.responses.create(
                model="gpt-4o",  
                instructions=SYSTEM_INSTRUCTIONS,
                conversation=st.session_state.conversation_id,
                input=[{"role": "user", "content": user_query}],
                store=True,
                tools=[{
                    "type": "file_search",
                    "vector_store_ids": ["vs_6ad8ec212788819181221d747227c4a1"] 
                }]
            )
            
            assistant_response = response.output_text
            response_placeholder.markdown(assistant_response)
            st.session_state.messages.append({"role": "assistant", "content": assistant_response})
            
            # Instantly pipe data into the persistent cloud spreadsheet tracker
            log_to_google_sheet(user_query, assistant_response)
            
        except Exception as e:
            response_placeholder.markdown(f"⚠️ API Error: {str(e)}")
