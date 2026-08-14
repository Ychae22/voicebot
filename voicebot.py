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
    
    # 💡 STT 모델을 3.1 flash lite로 지정
    model = genai.GenerativeModel('gemini-3.1-flash-lite')
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
    st.set_page_config(page_title="제미나이 음성/텍스트 비서", layout="wide")

    # 세션 상태 초기화
    if "chat" not in st.session_state:
        st.session_state["chat"] = []
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "check_reset" not in st.session_state:
        st.session_state["check_reset"] = False
    if "last_audio_len" not in st.session_state:
        st.session_state["last_audio_len"] = 0  # 중복 음성 처리 방지용

    st.header("✨ 제미나이(Gemini) AI 비서 프로그램")
    st.markdown("---")

    # 사이드바 설정
    with st.sidebar:
        gemini_api_key = st.text_input(label="Gemini API 키", placeholder="Enter Your Gemini API Key", type="password")
        st.markdown("---")
        
        # 💡 UI 옵션을 3.1 Flash Lite 하나로 깔끔하게 통일
        model_options = {
            "3.1 Flash Lite": "gemini-3.1-flash-lite"
        }
        
        selected_model_ui = st.radio(label="Gemini 모델 선택", options=list(model_options.keys()), index=0)
        model = model_options[selected_model_ui]
        
        st.markdown("---")
        
        if st.button(label="대화 초기화"):
            st.session_state["chat"] = []
            st.session_state["messages"] = []
            st.session_state["check_reset"] = True
            st.session_state["last_audio_len"] = 0
            st.rerun()

    # 화면 2분할
    col1, col2 = st.columns(2)
    
    user_question = "" # 음성이든 텍스트든 질문을 담을 변수

    with col1:
        st.subheader("질문하기 (음성 또는 텍스트)")
        
        # 1. 음성 입력 위젯
        audio = audiorecorder("🎤 클릭하여 녹음하기", "🔴 녹음 중...")
        
        # 2. 텍스트 입력 위젯 (Form을 사용하여 Enter 입력 시 한 번에 제출되도록 구성)
        with st.form(key="text_input_form", clear_on_submit=True):
            text_input = st.text_input("💬 텍스트로 질문하기", placeholder="여기에 질문을 입력하고 Enter를 누르세요.")
            submit_btn = st.form_submit_button(label="전송")

        # 초기화 상태 해제
        if st.session_state["check_reset"]:
            st.session_state["check_reset"] = False
            
        else:
            if not gemini_api_key and (len(audio) > 0 or submit_btn):
                st.error("좌측 사이드바에 Gemini API 키를 입력해주세요!")
            else:
                # 텍스트 입력이 제출된 경우 최우선으로 처리
                if submit_btn and text_input:
                    user_question = text_input
                    
                # 새로운 음성이 녹음된 경우 처리 (기존 녹음본 재실행 방지)
                elif len(audio) > 0 and len(audio) != st.session_state["last_audio_len"]:
                    st.session_state["last_audio_len"] = len(audio)
                    st.audio(audio.export().read())
                    
                    with st.spinner("음성을 텍스트로 변환 중..."):
                        user_question = STT(audio, gemini_api_key)

            # 질문이 접수되었으면 대화 내역에 추가
            if user_question:
                now = datetime.now().strftime("%H:%M")
                st.session_state["chat"].append(("user", now, user_question))
                st.session_state["messages"].append({"role": "user", "content": user_question})

    with col2:
        st.subheader("제미나이 답변")
        
        # 새로운 질문(user_question)이 들어왔을 때만 답변 생성
        if user_question:
            with st.spinner("제미나이가 생각 중입니다..."):
                response = ask_gemini(st.session_state["messages"], model, gemini_api_key)
            
            st.session_state["messages"].append({"role": "model", "content": response})
            now = datetime.now().strftime("%H:%M")
            st.session_state["chat"].append(("bot", now, response))

        # 채팅 UI 출력 (전체 대화 내역)
        for sender, time, message in st.session_state["chat"]:
            if sender == "user":
                st.write(f'<div style="display:flex;align-items:center;"><div style="background-color:#007AFF;color:white;border-radius:12px;padding:8px 12px;margin-right:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
            else:
                st.write(f'<div style="display:flex;align-items:center;justify-content:flex-end;"><div style="background-color:lightgray;color:black;border-radius:12px;padding:8px 12px;margin-left:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
            st.write("")
        
        # 새로운 답변이 방금 생성된 경우에만 TTS(음성 읽어주기) 실행
        if user_question:
            TTS(response)

if __name__ == "__main__":
    main()
