# app.py
import streamlit as st
import os

from database_setup import setup_sample_database
from sql_engine import SafeSQLGraphEngine

# Set up page configurations
st.set_page_config(page_title="QueryWorks: Conversational SQL Agent", page_icon="💼", layout="centered")

if not os.environ.get("ANTHROPIC_API_KEY"):
    st.error("Please set the ANTHROPIC_API_KEY environment variable to run this application.")
    st.stop()

# Initialize the database and engine once using Streamlit caching
@st.cache_resource
def get_engine():
    # Calling the setup function from database_setup.py
    db_file = setup_sample_database("organization_vault.db")
    # Initializing the engine from sql_engine.py
    return SafeSQLGraphEngine(db_file)

try:
    engine = get_engine()
except Exception as e:
    st.error(f"Failed to initialize the graph engine: {e}")
    st.stop()

# App Header Layout
st.title("💼 QueryWorks")
st.caption("Application Modernization Semantic Layer — Query legacy databases securely using natural language.")
st.divider()

# Initialize chat history session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your semantic data assistant. Ask me anything about our legacy entities or transaction behaviors."}
    ]

# Display historical messages from session state
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if user_prompt := st.chat_input("e.g., How much total money have we spent with Apex Logistics?"):
    
    # Append and display user message
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Generate assistant response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        with st.spinner("Analyzing database schema and generating secure response..."):
            # Call your LangGraph engine directly
            answer = engine.ask(user_prompt)
            
        response_placeholder.markdown(answer)
        
    # Append assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": answer})