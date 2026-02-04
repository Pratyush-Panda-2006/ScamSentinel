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

# --- ASSETS & ANIMATIONS ---
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=5) # Add a timeout
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None

# Load assets (Shield & Scanning Radar)
lottie_shield = load_lottieurl("https://lottie.host/932e655a-e7f7-466d-8868-245842c9533b/3s2t3a9k2.json")
lottie_scanning = load_lottieurl("https://assets10.lottiefiles.com/packages/lf20_w51pcehl.json")

if lottie_shield:
    st_lottie(lottie_shield, height=150, key="shield_anim")
else:
    st.info("🛡️ (Shield Animation Offline)")

# --- THEME ENGINE (CSS) ---
# We use Session State to hold the theme preference
if 'theme' not in st.session_state:
    st.session_state.theme = 'Dark'

def apply_custom_css(theme):
    if theme == 'Dark':
        bg_color = "#0E1117"
        text_color = "#FAFAFA"
        card_bg = "rgba(38, 39, 48, 0.7)" # Glassmorphism Dark
        border_color = "#FF4B4B"
        accent_color = "#00FFAA" # Cyber Green
    else:
        bg_color = "#F0F2F6"
        text_color = "#31333F"
        card_bg = "rgba(255, 255, 255, 0.9)" # Glassmorphism Light
        border_color = "#FF4B4B"
        accent_color = "#0068C9" # Professional Blue

    st.markdown(f"""
    <style>
        /* Main Background override */
        .stApp {{
            background-color: {bg_color};
            color: {text_color};
        }}
        
        /* Glassmorphism Cards for Intelligence */
        .intel-card {{
            background-color: {card_bg};
            padding: 20px;
            border-radius: 15px;
            border-left: 5px solid {border_color};
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 15px;
            backdrop-filter: blur(10px);
            transition: transform 0.3s ease;
        }}
        .intel-card:hover {{
            transform: translateY(-5px);
        }}
        
        /* Metric Styling */
        .metric-label {{
            font-size: 0.8rem;
            color: {text_color};
            opacity: 0.8;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .metric-value {{
            font-size: 1.2rem;
            font-weight: bold;
            color: {accent_color};
            font-family: 'Courier New', monospace;
        }}
        
        /* Chat Input Styling */
        .stTextInput > div > div > input {{
            background-color: {card_bg};
            color: {text_color};
            border-radius: 10px;
        }}
    </style>
    """, unsafe_allow_html=True)

# --- BACKEND LOGIC (Unchanged) ---
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
        client = genai.Client(api_key=api_key)
        system_instruction = """
        You are a defensive AI Honeypot designed to waste a scammer's time. 
        Your Persona: You are an elderly, non-technical person named 'Amit'. 
        Guidelines:
        1. Never admit you are an AI. 
        2. Act confused, worried, and eager to resolve the 'issue'.
        3. Deliberately make small mistakes.
        4. Ask many clarifying questions.
        5. Your goal is to get the scammer to reveal more banking details or links.
        """
        model_id = "gemini-3-flash-preview"
        full_prompt = f"CONVERSATION HISTORY:\n{conversation_history}\n\nSCAMMER SAYS: {user_input}\n\nAMIT (YOU) SAYS:"
        
        response = client.models.generate_content(
            model=model_id,
            contents=full_prompt,
            config=types.GenerateContentConfig(system_instruction=system_instruction)
        )
        return response.text
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# --- SIDEBAR UI ---
with st.sidebar:
    st_lottie(lottie_shield, height=150, key="shield_anim")
    st.markdown("## ⚙️ System Control")
    
    # Theme Toggle
    theme_choice = st.radio("Display Mode", ["Dark", "Light"], horizontal=True)
    apply_custom_css(theme_choice) # Apply the CSS based on choice
    
    api_key = st.text_input("Gemini API Key", type="password", help="Required for AI Logic")
    
    st.divider()
    
    if st.button("🗑️ Purge Session Data", use_container_width=True):
        st.session_state.messages = []
        st.session_state.extractor = IntelligenceExtractor()
        st.rerun()
    
    st.markdown("---")
    st.caption("🔒 Status: **Active Monitoring**")
    st.caption("v2.5.0 | Secure Connection")

# --- MAIN UI LAYOUT ---
# Header Section
col_head1, col_head2 = st.columns([0.8, 0.2])
with col_head1:
    st.title("🛡️ ScamSentinel")
    st.markdown("#### **Autonomous Cyber-Defense & Intelligence Extraction Agent**")
    st.markdown("Interact as a scammer. The AI will counter-engage and extract threat data.")
with col_head2:
    if theme_choice == 'Dark':
        st_lottie(lottie_scanning, height=100, key="scan_anim")

st.divider()

# Logic Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "extractor" not in st.session_state:
    st.session_state.extractor = IntelligenceExtractor()

# Two-Column Layout (Chat vs Intel)
col_chat, col_intel = st.columns([0.65, 0.35], gap="large")

# --- LEFT COLUMN: Chat Interface ---
with col_chat:
    st.subheader("💬 Live Interception Channel")
    
    # Message Container
    chat_container = st.container(height=500)
    with chat_container:
        for message in st.session_state.messages:
            avatar = "💀" if message["role"] == "user" else "🛡️"
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])

    # Input Area
    if prompt := st.chat_input("Type your scam message here..."):
        if not api_key:
            st.warning("⚠️ Access Denied: Please enter API Key in System Control.")
        else:
            # User Msg
            st.session_state.messages.append({"role": "user", "content": prompt})
            with chat_container:
                with st.chat_message("user", avatar="💀"):
                    st.markdown(prompt)

            # Extract Intel
            st.session_state.extractor.scan(prompt)

            # AI Msg
            with st.spinner("⚡ AI Agent is formulating counter-strategy..."):
                history_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
                ai_reply = get_gemini_response(api_key, history_text, prompt)
                time.sleep(0.8) # Organic delay
                
                st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                with chat_container:
                    with st.chat_message("assistant", avatar="🛡️"):
                        st.markdown(ai_reply)
            
            # Rerun to update the Intel Panel instantly
            st.rerun()

# --- RIGHT COLUMN: Intelligence Dashboard ---
with col_intel:
    st.subheader("📡 Threat Intelligence")
    data = st.session_state.extractor.extracted_data
    
    # Live Stats Row
    m1, m2 = st.columns(2)
    with m1:
        st.markdown(f"""
        <div class="intel-card" style="text-align: center; padding: 10px;">
            <div class="metric-value">{len(data['upi_ids'])}</div>
            <div class="metric-label">UPI IDs</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="intel-card" style="text-align: center; padding: 10px;">
            <div class="metric-value">{len(data['phishing_links'])}</div>
            <div class="metric-label">Links</div>
        </div>
        """, unsafe_allow_html=True)

    # Detailed Cards
    if data["upi_ids"]:
        st.markdown('<div class="intel-card">', unsafe_allow_html=True)
        st.markdown("**💰 Captured Financial IDs**")
        for upi in data["upi_ids"]:
            st.code(upi, language="text")
        st.markdown('</div>', unsafe_allow_html=True)
        
    if data["phishing_links"]:
        st.markdown('<div class="intel-card">', unsafe_allow_html=True)
        st.markdown("**🔗 Malicious Domains**")
        for link in data["phishing_links"]:
            st.code(link, language="text")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Phone Numbers
    if data["phone_numbers"]:
        st.markdown('<div class="intel-card">', unsafe_allow_html=True)
        st.markdown("**📱 Contact Traces**")
        for phone in data["phone_numbers"]:
            st.code(phone, language="text")
        st.markdown('</div>', unsafe_allow_html=True)

    if not any(data.values()):
        st.info("System Idle. Waiting for incoming threats...")
        st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExYzJ3cHR5aWZ5cnh3amN4ZW54aDJ4bHpjZ3I3dG94eHZ0c2Y4eGZ1diZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/LpSf6D97vB73gS75q4/giphy.gif", caption="Scanning Network...")