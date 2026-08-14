import streamlit as st
from audiorecorder import audiorecorder
import google.generativeai as genai
import os
from datetime import datetime
from gtts import gTTS
import base64

##### 1. 기능 구현 함수 #####

# 음성을 텍스트로 변환 (STT) - 제미나이 활용
def STT(audio, apikey):
    filename = 'input.mp3'
    audio.export(filename, format="mp3")
    
    genai.configure(api_key=apikey)
    audio_file = genai.upload_file(path=filename)
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content([
        "이 오디오에서 들리는 말을 한국어 텍스트로만 정확하게 받아적어줘. 다른 말은 절대 덧붙이지 마.", 
        audio_file
    ])
    
    os.remove(filename)
    genai.delete_file(audio_file.name)
    
    return response.text.strip()

# 텍스트 답변 생성 (LLM) - 제미나이 채팅 활용
def ask_gemini(messages, model_name, apikey):
    genai.configure(api_key=apikey)
    model = genai.GenerativeModel(model_name)
    
    gemini_history = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        gemini_history.append({"role": role, "parts": [msg["content"]]})
    
    history = gemini_history[:-1]
    current_msg = gemini_history[-1]["parts"][0]
    
    chat = model.start_chat(history=history)
    response = chat.send_message(current_msg)
    
    return response.text

# 텍스트를 음성으로 재생 (TTS) - gTTS 활용
def TTS(response):
    filename = "output.mp3"
    tts = gTTS(text=response, lang="ko")
    tts.save(filename)
    
    with open(filename, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay="True">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)
    os.remove(filename)

##### 2. 메인 웹 화면 구현 #####
def main():
    st.set_page_config(page_title="제미나이 음성 비서", layout="wide")

    # 세션 상태 초기화
    if "chat" not in st.session_state:
        st.session_state["chat"] = []
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "check_reset" not in st.session_state:
        st.session_state["check_reset"] = False

    st.header("✨ 제미나이(Gemini) 음성 비서 프로그램")
    st.markdown("---")

    # 사이드바 설정
    with st.sidebar:
        gemini_api_key = st.text_input(label="Gemini API 키", placeholder="Enter Your Gemini API Key", type="password")
        st.markdown("---")
        
        # 💡 UI에 보여줄 이름과 실제 API 모델명을 매핑(연결)해줍니다.
        model_options = {
            "1.5 Flash-8B (가장 빠른 답변)": "gemini-1.5-flash-8b",
            "1.5 Flash (무엇이든 도움)": "gemini-1.5-flash",
            "1.5 Pro (고급 수학 및 코딩)": "gemini-1.5-pro"
        }
        
        # 사용자는 익숙한 이름을 선택하지만, 코드 내부에서는 API용 이름을 사용합니다.
        selected_model_ui = st.radio(label="Gemini 모델 선택", options=list(model_options.keys()), index=2) # 기본값을 1.5 Pro로 설정
        model = model_options[selected_model_ui]
        
        st.markdown("---")
        
        if st.button(label="대화 초기화"):
            st.session_state["chat"] = []
            st.session_state["messages"] = []
            st.session_state["check_reset"] = True

    # 화면 2분할
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("마이크로 질문하기")
        audio = audiorecorder("🎤 클릭하여 녹음하기", "🔴 녹음 중...")
        
        if (audio.duration_seconds > 0) and not st.session_state["check_reset"]:
            if not gemini_api_key:
                st.error("좌측 사이드바에 Gemini API 키를 입력해주세요!")
                return
            
            st.audio(audio.export().read())
            
            with st.spinner("음성을 텍스트로 변환 중..."):
                question = STT(audio, gemini_api_key)
            
            now = datetime.now().strftime("%H:%M")
            st.session_state["chat"].append(("user", now, question))
            st.session_state["messages"].append({"role": "user", "content": question})

    with col2:
        st.subheader("제미나이 답변")
        if (audio.duration_seconds > 0) and not st.session_state["check_reset"]:
            with st.spinner("제미나이가 생각 중입니다..."):
                response = ask_gemini(st.session_state["messages"], model, gemini_api_key)
            
            st.session_state["messages"].append({"role": "model", "content": response})
            now = datetime.now().strftime("%H:%M")
            st.session_state["chat"].append(("bot", now, response))

        # 채팅 UI 출력
        for sender, time, message in st.session_state["chat"]:
            if sender == "user":
                st.write(f'<div style="display:flex;align-items:center;"><div style="background-color:#007AFF;color:white;border-radius:12px;padding:8px 12px;margin-right:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
            else:
                st.write(f'<div style="display:flex;align-items:center;justify-content:flex-end;"><div style="background-color:lightgray;color:black;border-radius:12px;padding:8px 12px;margin-left:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
            st.write("")
        
        if (audio.duration_seconds > 0) and not st.session_state["check_reset"]:
            TTS(response)

if __name__ == "__main__":
    main()