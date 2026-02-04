import streamlit as st
from google import genai
from google.genai import types
import re
import time
import requests
from streamlit_lottie import st_lottie

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="ScamSentinel | AI Defense System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ASSETS & ANIMATIONS (WITH SAFETY WRAPPERS) ---
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=5) 
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None

# Loading updated 2026-stable Lottie links
lottie_shield = load_lottieurl("https://lottie.host/932e655a-e7f7-466d-8868-245842c9533b/3s2t3a9k2.json")
lottie_scanning = load_lottieurl("https://lottie.host/85501865-0466-486a-8531-98781912f22b/O6Kq0B3D9h.json")

# --- THEME ENGINE (CSS) ---
if 'theme' not in st.session_state:
    st.session_state.theme = 'Dark'

def apply_custom_css(theme):
    if theme == 'Dark':
        bg_color, text_color, card_bg = "#0E1117", "#FAFAFA", "rgba(38, 39, 48, 0.7)"
        border_color, accent_color = "#FF4B4B", "#00FFAA"
    else:
        bg_color, text_color, card_bg = "#F0F2F6", "#31333F", "rgba(255, 255, 255, 0.9)"
        border_color, accent_color = "#FF4B4B", "#0068C9"

    st.markdown(f"""
    <style>
        .stApp {{ background-color: {bg_color}; color: {text_color}; }}
        .intel-card {{
            background-color: {card_bg}; padding: 20px; border-radius: 15px;
            border-left: 5px solid {border_color}; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 15px; backdrop-filter: blur(10px); transition: transform 0.3s ease;
        }}
        .intel-card:hover {{ transform: translateY(-5px); }}
        .metric-value {{ font-size: 1.2rem; font-weight: bold; color: {accent_color}; font-family: 'Courier New', monospace; }}
        .stTextInput > div > div > input {{ background-color: {card_bg}; color: {text_color}; border-radius: 10px; }}
    </style>
    """, unsafe_allow_html=True)

# --- BACKEND LOGIC ---
class IntelligenceExtractor:
    def __init__(self):
        self.extracted_data = {"upi_ids": set(), "phishing_links": set(), "phone_numbers": set()}

    def scan(self, text):
        upi_pattern = r'[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}'
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        phone_pattern = r'\+?[0-9]{10,12}'
        
        self.extracted_data["upi_ids"].update(re.findall(upi_pattern, text))
        self.extracted_data["phishing_links"].update(re.findall(url_pattern, text))
        self.extracted_data["phone_numbers"].update(re.findall(phone_pattern, text))
        return self.extracted_data

def get_gemini_response(api_key, conversation_history, user_input):
    try:
        client = genai.Client(api_key=api_key)
        system_instruction = "You are an elderly, non-technical victim named Amit. Be confused and waste the scammer's time to get their bank details."
        
        # FIX: Using the correct 2026 stable model name
        model_id = "gemini-3-flash-preview" 
        
        full_prompt = f"HISTORY:\n{conversation_history}\n\nSCAMMER: {user_input}\n\nAMIT:"
        response = client.models.generate_content(
            model=model_id,
            contents=full_prompt,
            config=types.GenerateContentConfig(system_instruction=system_instruction)
        )
        return response.text
    except Exception as e:
        return f"⚠️ Connection Error: {str(e)}"

# --- SIDEBAR UI ---
with st.sidebar:
    if lottie_shield:
        st_lottie(lottie_shield, height=150, key="shield_anim")
    else:
        st.title("🛡️")
        
    st.markdown("## ⚙️ System Control")
    theme_choice = st.radio("Display Mode", ["Dark", "Light"], horizontal=True)
    apply_custom_css(theme_choice)
    
    api_key = st.text_input("Gemini API Key", type="password")
    if st.button("🗑️ Purge Session Data", use_container_width=True):
        st.session_state.messages, st.session_state.extractor = [], IntelligenceExtractor()
        st.rerun()

# --- MAIN UI ---
st.title("🛡️ ScamSentinel")
st.markdown("#### **Autonomous Cyber-Defense & Intelligence Extraction Agent**")

if "messages" not in st.session_state: st.session_state.messages = []
if "extractor" not in st.session_state: st.session_state.extractor = IntelligenceExtractor()

col_chat, col_intel = st.columns([0.65, 0.35], gap="large")

with col_chat:
    chat_container = st.container(height=500)
    with chat_container:
        for m in st.session_state.messages:
            with st.chat_message(m["role"], avatar="💀" if m["role"]=="user" else "🛡️"):
                st.markdown(m["content"])

    if prompt := st.chat_input("Enter message..."):
        if not api_key: st.warning("Enter API Key in Sidebar.")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.extractor.scan(prompt)
            with st.spinner("Counter-engaging..."):
                hist = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                reply = get_gemini_response(api_key, hist, prompt)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()

with col_intel:
    st.subheader("📡 Threat Intelligence")
    data = st.session_state.extractor.extracted_data
    
    # Visual Metrics
    m1, m2 = st.columns(2)
    m1.markdown(f'<div class="intel-card"><div class="metric-value">{len(data["upi_ids"])}</div>UPI IDs</div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="intel-card"><div class="metric-value">{len(data["phishing_links"])}</div>Links</div>', unsafe_allow_html=True)

    for label, key in [("💰 Financial IDs", "upi_ids"), ("🔗 Malicious Domains", "phishing_links"), ("📱 Contact Traces", "phone_numbers")]:
        if data[key]:
            st.markdown(f'<div class="intel-card">**{label}**', unsafe_allow_html=True)
            for item in data[key]: st.code(item, language="text")
            st.markdown('</div>', unsafe_allow_html=True)