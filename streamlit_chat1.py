import streamlit as st
from streamlit_chat import message
from scipy.io.wavfile import write
import requests
import sounddevice as sd
import streamlit_webrtc as webrtc
import whisper
from elevenlabs import generate, play


model = whisper.load_model("tiny")


st.set_page_config(
    page_title="Streamlit Chat - Demo",
    page_icon=":robot:"
)

API_URL = "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"
headers = {"Authorization": "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"}

st.header("Chat: Demo")

if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

def get_text():
    input_text = st.text_input("You: ","", key="input")
    return input_text 

input_mode = st.radio("Select input mode", ("Text", "Voice"))
if 'first' not in st.session_state:
    st.session_state['first'] = True

if input_mode == "Text":
    user_input = get_text()

    if st.session_state['first']:
        st.session_state['chat_history'].append(('user', ""))
        st.session_state['chat_history'].append(('bot', "How can I help you?"))
        st.session_state['first'] = False

    if user_input != "":
        output = {
        "generated_text": "Hi, my name is Bella, nice to meet you ",
        }
        audio = generate(
        text="Hola, que tal?!",
        voice="Bella",
        model="eleven_multilingual_v1"
        )
        play(audio)

        st.session_state['chat_history'].append(('user', user_input))
        st.session_state['chat_history'].append(('bot', output["generated_text"]))

    if st.session_state['chat_history']:
        for i in range(len(st.session_state['chat_history'])-1, -1, -2):
            message(st.session_state['chat_history'][i][1], key=str(i), avatar_style="bottts", seed=2)
            message(st.session_state['chat_history'][i-1][1], is_user=True, key=str(i) + '_user', avatar_style="avataaars-neutral", seed=10)

elif input_mode == "Voice":
    st.button("Record/Stop")
    # Recording audio
    if 'audio_frames' not in st.session_state:
        st.session_state['audio_frames'] = []
    audio_frames = st.session_state['audio_frames']

    is_recording = st.session_state.get('is_recording', False)
    if is_recording:
        st.write("Recording audio...")
        audio_frames.append(sd.rec(int(5 * 22050), samplerate=22050, channels=1))
    else:
        if audio_frames:
            st.write("Recording stopped.", len(audio_frames))
            audio_frames = audio_frames[-1]
            write("output.mp3", 22050, audio_frames)
            result = model.transcribe("output.mp3")
            output = {
            "generated_text": "Hi, my name is Bella, nice to meet you ",
            }
            st.session_state['chat_history'].append(('user', result["text"]))
            st.session_state['chat_history'].append(('bot', output["generated_text"]))
            #st.audio(audio_frames, sample_rate=22050)
        else: 
            st.write("Stopped")
            st.write(len(audio_frames))
    if is_recording:
        st.session_state['is_recording'] = False

    else:
        st.session_state['is_recording'] = True
    if st.session_state['chat_history']:
        for i in range(len(st.session_state['chat_history'])-1, -1, -2):
            message(st.session_state['chat_history'][i][1], key=str(i), avatar_style="bottts", seed=2)
            message(st.session_state['chat_history'][i-1][1], is_user=True, key=str(i) + '_user', avatar_style="avataaars-neutral", seed=10)
    else:
        st.write("There is no chat history yet.")