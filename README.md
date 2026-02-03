# 🛡️ ScamSentinel: Agentic AI Honeypot

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-red)
![Gemini](https://img.shields.io/badge/AI-Google%20Gemini-orange)

**ScamSentinel** is a real-time, interactive AI agent designed for **Defensive Intelligence Gathering**. 

Unlike passive blockers, this system uses **Google Gemini (LLM)** to actively engage scammers. It adopts a believable persona (e.g., a confused elderly victim) to prolong conversations, tricking attackers into revealing actionable threat intelligence like **UPI IDs**, **Bank Accounts**, and **Phishing Links**.

## 🚀 Key Features

- **🧠 Active Engagement:** Uses `Gemini-Pro` to generate context-aware, "victim-like" responses that keep scammers hooked.
- **🕵️ Real-Time Extraction:** Instantly parses chat logs using Regex to capture IOCs (Indicators of Compromise) as they are typed.
- **🛡️ Defensive Persona:** The AI is prompted to make "human mistakes" (typos, confusion) to lower the scammer's guard.
- **📊 Live Dashboard:** A beautiful Streamlit UI to watch the interception and extraction happen in real-time.

## 📸 How It Works
1. **The Trigger:** You (acting as the scammer for testing) send a message: *"Pay your electricity bill to officer@okaxis immediately."*
2. **The Defense:** The AI analyzes the threat and replies: *"I am scared! Please don't cut my power. How do I pay? I am not good with phone apps."*
3. **The Capture:** The system silently logs `officer@okaxis` into the Intelligence Database.

## 🛠️ Tech Stack
- **Frontend:** Streamlit
- **AI Core:** Google Generative AI (Gemini Pro)
- **Logic:** Python (Regex for extraction)

## 📦 Installation & Usage

1. **Clone the repository**
   ```bash
   git clone [https://github.com/Pratyush-Panda-2006/ScamSentinel.git](https://github.com/Pratyush-Panda-2006/ScamSentinel.git)
   cd ScamSentinel
