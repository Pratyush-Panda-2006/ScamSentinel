import streamlit as st
from google import genai
from google.genai import types
import re
import requests
from streamlit_lottie import st_lottie
from streamlit_audiorecorder import audiorecorder
from gtts import gTTS
from io import BytesIO

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="ScamSentinel | Voice Defense",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ASSETS & CSS ---
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200: return None
        return r.json()
    except Exception: return None

# "Speaking" animation for the AI
lottie_voice = load_lottieurl("https://lottie.host/6b3e6955-e7f7-466d-8868-245842c9533b/voice_wave.json")
# Default shield
lottie_shield = load_lottieurl("https://lottie.host/932e655a-e7f7-466d-8868-245842c9533b/3s2t3a9k2.json")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .stAudio { width: 100%; }
    /* Custom Card Style for Intel */
    .intel-card {
        background-color: rgba(38, 39, 48, 0.7);
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #FF4B4B;
        margin-bottom: 10px;
    }
    .transcript-box {
        background-color: #1E1E1E;
        padding: 15px;
        border-radius: 10px;
        height: 400px;
        overflow-y: scroll;
        border: 1px solid #333;
    }
    .user-msg { color: #00FFAA; margin-bottom: 5px; font-weight: bold;}
    .ai-msg { color: #FAFAFA; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# --- BACKEND LOGIC ---
class IntelligenceExtractor:
    def __init__(self):
        self.extracted_data = {"upi_ids": set(), "phishing_links": set(), "phone_numbers": set()}

    def scan(self, text):
        # Scans text for patterns
        self.extracted_data["upi_ids"].update(re.findall(r'[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}', text))
        self.extracted_data["phishing_links"].update(re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text))
        self.extracted_data["phone_numbers"].update(re.findall(r'\+?[0-9]{10,12}', text))
        return self.extracted_data

def get_gemini_voice_response(api_key, conversation_history, audio_bytes):
    try:
        client = genai.Client(api_key=api_key)
        # We use a model capable of understanding audio
        model_id = "gemini-1.5-flash" 
        
        system_instruction = (
            "You are an AI defense agent named 'Sentinel'. You are speaking to a potential scammer on the phone. "
            "Your goal is to detect if they are a scammer by asking probing questions, but pretend to be a naive victim named Amit. "
            "Keep your responses short (1-2 sentences) and conversational so the synthesis sounds natural."
        )

        # Prepare the prompt with history and new audio
        contents = []
        if conversation_history:
            # We summarize history as text context
            contents.append(types.Content(role="user", parts=[types.Part.from_text(text=f"PREVIOUS CONVERSATION CONTEXT:\n{conversation_history}")]))
        
        # Add the new audio clip
        contents.append(types.Content(role="user", parts=[
            types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
            types.Part.from_text(text="Respond to this audio spoken by the caller.")
        ]))

        response = client.models.generate_content(
            model=model_id,
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=system_instruction)
        )
        return response.text
    except Exception as e:
        return f"System Error: {str(e)}"

def text_to_speech(text):
    """Converts text to audio bytes using gTTS"""
    try:
        tts = gTTS(text=text, lang='en', tld='co.in') # 'co.in' gives an Indian English accent
        audio_fp = BytesIO()
        tts.write_to_fp(audio_fp)
        return audio_fp.getvalue()
    except Exception:
        return None

# --- STATE MANAGEMENT ---
if "messages" not in st.session_state: st.session_state.messages = []
if "extractor" not in st.session_state: st.session_state.extractor = IntelligenceExtractor()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Settings")
    api_key = st.text_input("Gemini API Key", type="password")
    
    st.info("ℹ️ **Instructions:**\n1. Enter API Key.\n2. Click the Mic button to talk.\n3. The AI will listen and reply.")
    
    if st.button("🗑️ Reset Call"):
        st.session_state.messages = []
        st.session_state.extractor = IntelligenceExtractor()
        st.rerun()
        
    st.divider()
    
    # Intel Dashboard in Sidebar for cleaner Voice UI
    st.subheader("📡 Live Intel")
    data = st.session_state.extractor.extracted_data
    
    if data["upi_ids"]:
        st.markdown(f'<div class="intel-card">💰 <b>UPI IDs Found:</b><br>{", ".join(data["upi_ids"])}</div>', unsafe_allow_html=True)
    if data["phishing_links"]:
        st.markdown(f'<div class="intel-card">🔗 <b>Links Found:</b><br>{", ".join(data["phishing_links"])}</div>', unsafe_allow_html=True)
    if not (data["upi_ids"] or data["phishing_links"]):
        st.caption("No threats detected yet...")

# --- MAIN UI ---
st.title("🛡️ ScamSentinel | Live Voice Agent")

col_visual, col_transcript = st.columns([0.4, 0.6])

with col_visual:
    st.markdown("### 📞 Active Call")
    # Using Lottie to simulate a call interface
    if lottie_shield:
        st_lottie(lottie_voice if len(st.session_state.messages) > 0 else lottie_shield, height=200, key="status_anim")
    
    st.write(" ")
    st.write(" ")
    
    # --- VOICE INPUT ---
    # This creates a button that records when held/clicked
    audio_input = audiorecorder("🔴 TAP TO SPEAK", "⏹️ LISTENING...")

    if len(audio_input) > 0:
        if not api_key:
            st.error("Please enter your API Key in the sidebar first.")
        else:
            # 1. Process Audio
            with st.spinner("Analyzing audio pattern..."):
                # Save User Audio to state (optional, just for logic)
                audio_bytes = audio_input.export().read()
                
                # Context string for the AI
                hist_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                
                # Get Response from Gemini
                reply_text = get_gemini_voice_response(api_key, hist_text, audio_bytes)
                
                # Scan the AI's response (and implied user text) for intel
                # Note: Since we don't have user STT text, we scan the AI's response in case it repeats details
                st.session_state.extractor.scan(reply_text)
                
                # Append to history
                st.session_state.messages.append({"role": "user", "content": "🎤 [Audio Message Sent]"})
                st.session_state.messages.append({"role": "assistant", "content": reply_text})

            # 2. Play Response
            reply_audio = text_to_speech(reply_text)
            if reply_audio:
                st.audio(reply_audio, format="audio/mp3", autoplay=True)

with col_transcript:
    st.markdown("### 📝 Live Transcript")
    
    # Custom container for the transcript
    transcript_html = '<div class="transcript-box">'
    if not st.session_state.messages:
        transcript_html += '<div style="color: #666; text-align: center; padding-top: 150px;">Waiting for call to start...</div>'
    else:
        for msg in reversed(st.session_state.messages):
            if msg['role'] == 'user':
                transcript_html += f'<div class="user-msg">YOU (Caller)</div><div>{msg["content"]}</div><hr style="border-color: #333;">'
            else:
                transcript_html += f'<div class="ai-msg"><span style="color: #FF4B4B">AMIT (AI Agent)</span><br>{msg["content"]}</div>'
    transcript_html += '</div>'
    
    st.markdown(transcript_html, unsafe_allow_html=True)
