import streamlit as st
from audiorecorder import audiorecorder
import google.generativeai as genai
import os
from datetime import datetime
from gtts import gTTS
import base64

##### 1. 기능 구현 함수 #####

# 음성을 텍스트로 변환 (STT) - 제미나이 활용
def STT(audio, apikey, model_name):
    filename = 'input.mp3'
    audio.export(filename, format="mp3")
    
    genai.configure(api_key=apikey)
    audio_file = genai.upload_file(path=filename)
    
    try:
        # 지정된 모델 사용 (만약 3.1 flash lite가 없는 모델이면 여기서 에러를 잡습니다)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content([
            "이 오디오에서 들리는 말을 한국어 텍스트로만 정확하게 받아적어줘. 다른 말은 절대 덧붙이지 마.", 
            audio_file
        ])
        result_text = response.text.strip()
    except Exception as e:
        # API 에러 발생 시 프로그램이 멈추지 않고 에러 메시지 반환
        result_text = f"[STT 에러 발생] 음성 인식 중 문제가 발생했습니다. 모델명({model_name})이 올바른지 확인해주세요. (상세: {e})"
    finally:
        # 성공하든 실패하든 생성된 임시 파일은 확실히 삭제
        if os.path.exists(filename):
            os.remove(filename)
        try:
            genai.delete_file(audio_file.name)
        except:
            pass
            
    return result_text

# 텍스트 답변 생성 (LLM) - 제미나이 채팅 활용
def ask_gemini(messages, model_name, apikey):
    genai.configure(api_key=apikey)
    
    try:
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
    except Exception as e:
        return f"[답변 에러 발생] 제미나이가 답변을 생성하지 못했습니다. (상세: {e})"

# 텍스트를 음성으로 재생 (TTS) - gTTS 활용
def TTS(response):
    # 에러 메시지인 경우 읽어주지 않도록 예외 처리
    if "[에러 발생]" in response or "[STT 에러 발생]" in response:
        return
        
    filename = "output.mp3"
    try:
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
    except Exception as e:
        st.error(f"TTS(음성 변환) 오류: {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

##### 2. 메인 웹 화면 구현 #####
def main():
    st.set_page_config(page_title="제미나이 음성/텍스트 비서", layout="wide")

    if "chat" not in st.session_state:
        st.session_state["chat"] = []
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "check_reset" not in st.session_state:
        st.session_state["check_reset"] = False
    if "last_audio_len" not in st.session_state:
        st.session_state["last_audio_len"] = 0

    st.header("✨ 제미나이(Gemini) AI 비서 프로그램")
    st.markdown("---")

    with st.sidebar:
        gemini_api_key = st.text_input(label="Gemini API 키", placeholder="Enter Your Gemini API Key", type="password")
        st.markdown("---")
        
        # 💡 에러 확인을 위해 실제 공식 모델도 옵션으로 추가해두었습니다.
        model_options = {
            "3.1 Flash Lite (요청하신 모델)": "gemini-3.1-flash-lite",
            "1.5 Flash (공식 권장 모델)": "gemini-1.5-flash",
            "1.5 Flash-8B (공식 경량 모델)": "gemini-1.5-flash-8b"
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

    col1, col2 = st.columns(2)
    
    user_question = "" 
    input_type = ""

    with col1:
        st.subheader("질문하기 (음성 또는 텍스트)")
        
        audio = audiorecorder("🎤 클릭하여 녹음하기", "🔴 녹음 중...")
        
        with st.form(key="text_input_form", clear_on_submit=True):
            text_input = st.text_input("💬 텍스트로 질문하기", placeholder="여기에 질문을 입력하고 Enter를 누르세요.")
            submit_btn = st.form_submit_button(label="전송")

        if st.session_state["check_reset"]:
            st.session_state["check_reset"] = False
            
        else:
            if not gemini_api_key and (len(audio) > 0 or submit_btn):
                st.error("좌측 사이드바에 Gemini API 키를 입력해주세요!")
            else:
                if submit_btn and text_input:
                    user_question = text_input
                    input_type = "text"
                    
                elif len(audio) > 0 and len(audio) != st.session_state["last_audio_len"]:
                    st.session_state["last_audio_len"] = len(audio)
                    st.audio(audio.export().read())
                    
                    with st.spinner("음성을 텍스트로 변환 중..."):
                        # STT에도 사이드바에서 선택한 모델 변수(model)를 넘겨줍니다.
                        user_question = STT(audio, gemini_api_key, model)
                    input_type = "audio"

            # 음성 인식 과정에서 에러가 나면 곧바로 사용자에게 알려줍니다.
            if user_question:
                now = datetime.now().strftime("%H:%M")
                st.session_state["chat"].append(("user", now, user_question))
                # 에러 메시지가 아닐 때만 AI 기억(messages)에 저장합니다.
                if "[에러 발생]" not in user_question and "[STT 에러 발생]" not in user_question:
                    st.session_state["messages"].append({"role": "user", "content": user_question})

    with col2:
        st.subheader("제미나이 답변")
        
        if user_question:
            # STT 과정에서 에러가 났다면 답변 생성을 스킵합니다.
            if "[STT 에러 발생]" in user_question:
                response = "음성을 인식하지 못해 답변을 생성할 수 없습니다. 위 에러 메시지를 확인해주세요."
                st.session_state["chat"].append(("bot", datetime.now().strftime("%H:%M"), response))
            else:
                with st.spinner("제미나이가 생각 중입니다..."):
                    response = ask_gemini(st.session_state["messages"], model, gemini_api_key)
                
                if "[답변 에러 발생]" not in response:
                    st.session_state["messages"].append({"role": "model", "content": response})
                
                now = datetime.now().strftime("%H:%M")
                st.session_state["chat"].append(("bot", now, response))

        for sender, time, message in st.session_state["chat"]:
            if sender == "user":
                st.write(f'<div style="display:flex;align-items:center;"><div style="background-color:#007AFF;color:white;border-radius:12px;padding:8px 12px;margin-right:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
            else:
                st.write(f'<div style="display:flex;align-items:center;justify-content:flex-end;"><div style="background-color:lightgray;color:black;border-radius:12px;padding:8px 12px;margin-left:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
            st.write("")
        
        if user_question and input_type == "audio":
            TTS(response)

if __name__ == "__main__":
    main()
