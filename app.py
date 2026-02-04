import streamlit as st
from google import genai
from google.genai import types # Required for system instructions
import re
import time 

# --- Configuration & Styling ---
st.set_page_config(page_title="ScamSentinel: Live Gemini Honeypot", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .report-box { background-color: #262730; padding: 15px; border-radius: 10px; border-left: 5px solid #FF4B4B; margin-bottom: 10px;}
    .stTextInput > div > div > input { color: #ffffff; }
</style>
""", unsafe_allow_html=True)

class IntelligenceExtractor:
    def __init__(self):
        self.extracted_data = {
            "upi_ids": set(),
            "bank_accounts": set(),
            "phishing_links": set(),
            "phone_numbers": set()
        }

    def scan(self, text):
        upi_pattern = r'[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}'
        found_upis = re.findall(upi_pattern, text)
        self.extracted_data["upi_ids"].update(found_upis)

        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        found_urls = re.findall(url_pattern, text)
        self.extracted_data["phishing_links"].update(found_urls)
        
        phone_pattern = r'\+?[0-9]{10,12}'
        found_phones = re.findall(phone_pattern, text)
        self.extracted_data["phone_numbers"].update(found_phones)

        return self.extracted_data

def get_gemini_response(api_key, conversation_history, user_input):
    try:
        # 1. Initialize the modern Client
        client = genai.Client(api_key=api_key)
        
        # 2. Define the System Instruction (Persona)
        system_instruction = """
        You are a defensive AI Honeypot designed to waste a scammer's time. 
        Your Persona: You are an elderly, non-technical person named 'Amit'. 
        
        Guidelines:
        1. Never admit you are an AI. 
        2. Act confused, worried, and eager to resolve the 'issue' the scammer presents.
        3. Deliberately make small mistakes (e.g., "I clicked the button but nothing happened").
        4. Ask many clarifying questions to prolong the conversation.
        5. Your goal is to get the scammer to reveal more banking details or links.
        """
        
        # 3. Call the modern model (Gemini 3 Flash is current for 2026)
        model_id = "gemini-3-flash-preview"
        
        full_prompt = f"CONVERSATION HISTORY:\n{conversation_history}\n\nSCAMMER SAYS: {user_input}\n\nAMIT (YOU) SAYS:"
        
        response = client.models.generate_content(
            model=model_id,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction # New standard for personas
            )
        )
        return response.text
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# --- UI: Sidebar & Setup ---
st.sidebar.title("🔐 Configuration")
api_key = st.sidebar.text_input("Enter Google Gemini API Key", type="password")
st.sidebar.info("Get your key at: aistudio.google.com")

if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []
    st.session_state.extractor = IntelligenceExtractor()
    st.rerun()

# --- UI: Main Interface ---
st.title("🛡️ ScamSentinel: Interactive Honeypot")
st.markdown("### Test Mode: YOU act as the Scammer. The AI acts as the Victim.")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "extractor" not in st.session_state:
    st.session_state.extractor = IntelligenceExtractor()

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("💬 Live Interaction")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Type a scam message..."):
        if not api_key:
            st.error("Please enter your Gemini API Key first!")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            st.session_state.extractor.scan(prompt)

            with st.spinner("Agent is formulating a strategy..."):
                history_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
                ai_reply = get_gemini_response(api_key, history_text, prompt)
                
                time.sleep(1) 
                
                st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                with st.chat_message("assistant"):
                    st.markdown(ai_reply)

# --- Intelligence Column ---
with col2:
    st.subheader("🕵️ Real-Time Intelligence")
    data = st.session_state.extractor.extracted_data
    
    if data["upi_ids"]:
        st.markdown('<div class="report-box">', unsafe_allow_html=True)
        st.write("💰 **Captured UPI IDs:**")
        for upi in data["upi_ids"]:
            st.code(upi, language="text")
        st.markdown('</div>', unsafe_allow_html=True)
        
    if data["phishing_links"]:
        st.markdown('<div class="report-box">', unsafe_allow_html=True)
        st.write("🔗 **Captured Malicious Links:**")
        for link in data["phishing_links"]:
            st.code(link, language="text")
        st.markdown('</div>', unsafe_allow_html=True)

    if not data["upi_ids"] and not data["phishing_links"]:
        st.info("No threats detected yet.")