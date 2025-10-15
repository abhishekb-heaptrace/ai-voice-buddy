import streamlit as st
import requests
import pyttsx3
import threading
import speech_recognition as sr
import time

# Initialize components
@st.cache_resource
def init_components():
    recognizer = sr.Recognizer()
    tts_engine = pyttsx3.init()
    tts_engine.setProperty('rate', 180)
    return recognizer, tts_engine

recognizer, tts_engine = init_components()

# Streamlit config
st.set_page_config(page_title="AI Buddy", page_icon="🤖", layout="centered")

# Custom CSS
st.markdown("""
<style>
    .status-box { 
        background: #1a1a1a; 
        padding: 20px; 
        border-radius: 10px; 
        text-align: center;
        margin: 10px 0;
        border: 2px solid #00ff00;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'is_listening' not in st.session_state:
    st.session_state.is_listening = False
if 'status' not in st.session_state:
    st.session_state.status = "⏸️ Click Start to begin"
if 'listening_thread' not in st.session_state:
    st.session_state.listening_thread = None

st.title("🤖 AI Buddy - Always Listening")

# Status display
st.markdown(f"""
<div class="status-box">
    <h3>{st.session_state.status}</h3>
</div>
""", unsafe_allow_html=True)

# DeepSeek API function
def get_ai_response(user_text):
    try:
        st.session_state.conversation.append({"role": "user", "content": user_text})
        
        api_url = "https://api.deepseek.com/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer sk-a30acb38a6d24b9d803125e8cc2ea123"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": st.session_state.conversation,
            "stream": False,
            "max_tokens": 500
        }
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=20)
        
        if response.status_code == 200:
            response_data = response.json()
            ai_response = response_data['choices'][0]['message']['content']
            st.session_state.conversation.append({"role": "assistant", "content": ai_response})
            return ai_response
        else:
            return "I'm listening, please continue."
            
    except Exception as e:
        return "Let's keep talking."

# Function to speak text
def speak_text(text):
    def run_speech():
        try:
            clean_text = text.strip()
            if clean_text:
                tts_engine.say(clean_text)
                tts_engine.runAndWait()
        except Exception as e:
            print(f"Speech error: {e}")
    
    thread = threading.Thread(target=run_speech)
    thread.daemon = True
    thread.start()

# Continuous listening function
def continuous_listen():
    while st.session_state.is_listening:
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Update status
                st.session_state.status = "🎤 Listening... Speak now!"
                st.rerun()
                
                # Listen for speech
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                # Convert to text
                st.session_state.status = "🔄 Processing..."
                st.rerun()
                
                text = recognizer.recognize_google(audio)
                
                if text and text.strip():
                    st.session_state.status = "🤖 Thinking..."
                    st.rerun()
                    
                    # Get AI response
                    response = get_ai_response(text)
                    
                    # Speak response
                    speak_text(response)
                    
                    # Update status
                    st.session_state.status = "✅ Response spoken! Listening..."
                    st.rerun()
                    
        except sr.WaitTimeoutError:
            continue
        except sr.UnknownValueError:
            st.session_state.status = "🎤 Didn't catch that. Try again..."
            st.rerun()
            time.sleep(2)
            continue
        except Exception as e:
            st.session_state.status = f"❌ Error: {str(e)[:50]}..."
            st.rerun()
            time.sleep(2)
            continue

# Control buttons
col1, col2 = st.columns(2)

with col1:
    if st.button("🎤 START LISTENING", type="primary", use_container_width=True):
        st.session_state.is_listening = True
        st.session_state.status = "🎤 Starting microphone..."
        st.rerun()
        
        # Start listening thread
        if st.session_state.listening_thread is None or not st.session_state.listening_thread.is_alive():
            st.session_state.listening_thread = threading.Thread(target=continuous_listen, daemon=True)
            st.session_state.listening_thread.start()

with col2:
    if st.button("⏹️ STOP", use_container_width=True):
        st.session_state.is_listening = False
        st.session_state.status = "⏸️ Stopped"
        st.rerun()

# Conversation display
st.markdown("---")
st.subheader("💬 Conversation")

if st.session_state.conversation:
    for msg in st.session_state.conversation[-6:]:
        if msg['role'] == 'user':
            st.markdown(f"**👤 You:** {msg['content']}")
        else:
            st.markdown(f"**🤖 AI:** {msg['content']}")
else:
    st.info("No conversation yet. Click START and begin speaking!")

# Clear button
if st.button("🗑️ Clear Conversation"):
    st.session_state.conversation = []
    st.rerun()

# Instructions
with st.expander("🔧 Troubleshooting"):
    st.markdown("""
    **If not working:**
    1. Check microphone permissions in browser
    2. Ensure microphone is not muted
    3. Speak clearly and wait for status changes
    4. Replace API key in code
    5. Try speaking louder if "Didn't catch that" appears
    """)