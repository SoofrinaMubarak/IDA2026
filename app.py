import streamlit as st
from openai import OpenAI

# 1. Premium Page Configuration & Styling
st.set_page_config(page_title="IDA Presentation Chatbot", page_icon="🤖", layout="centered")

# Custom Branding Banner & CSS
st.markdown("""
    <style>
    .main-title {
        font-size: 42px !important;
        font-weight: 700;
        color: #1E3A8A; /* Premium Deep Blue */
        text-align: center;
        margin-bottom: 5px;
    }
    .subtitle {
        font-size: 18px !important;
        color: #4B5563; /* Slate Gray */
        text-align: center;
        margin-bottom: 30px;
    }
    .stChatMessage {
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Render headers
st.markdown('<div class="main-title">🤖 IDA Presentation AI Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Ask live questions directly about today\'s presentation slides!</div>', unsafe_allow_html=True)
st.divider()

# 2. Automated Cloud Credentials Check
# This fetches the key silently from the Streamlit settings dashboard
try:
    api_key = st.secrets["OPENAI_API_KEY"]
except KeyError:
    st.error("⚠️ Setup Error: OpenAI API Key is missing in the cloud dashboard settings.")
    st.stop()

# Initialize the OpenAI Client
client = OpenAI(api_key=api_key)

# 3. Persistent Conversation Management
if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_id" not in st.session_state:
    conversation = client.conversations.create()
    st.session_state.conversation_id = conversation.id

# System instruction context
SYSTEM_INSTRUCTIONS = """
You are an expert Subject Matter Expert chatbot for the IDA presentation. 
Answer user questions accurately. Keep your answers brief and limited to a maximum of 3 sentences 
so they are easy to read on mobile phones and presentation screens. 
If you don't know the answer based on the knowledge base, politely state that you do not know.
"""

# 4. Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Handle Live Interaction
if user_query := st.chat_input("Ask a question about the presentation..."):
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # 6. Call the Responses API
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        
        try:
            response = client.responses.create(
                model="gpt-5",  
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
            
        except Exception as e:
            response_placeholder.markdown(f"⚠️ API Error: {str(e)}")
