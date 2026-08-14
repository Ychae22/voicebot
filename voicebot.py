import streamlit as st
from audiorecorder import audiorecorder
import google.generativeai as genai
import os
from datetime import datetime
from gtts import gTTS
import base64

##### 1. 기능 구현 함수 #####

# 음성 -> 텍스트 (STT)
def STT(audio, apikey, model_name):
    filename = 'input.mp3'
    audio.export(filename, format="mp3")
    
    genai.configure(api_key=apikey)
    
    try:
        model = genai.GenerativeModel(model_name)
        
        with open(filename, "rb") as f:
            audio_bytes = f.read()
            
        audio_data = {
            "mime_type": "audio/mp3",
            "data": audio_bytes
        }
        
        response = model.generate_content([
            "이 오디오에서 들리는 말을 한국어 텍스트로만 정확하게 받아적어줘. 다른 말은 절대 덧붙이지 마.", 
            audio_data
        ])
        result_text = response.text.strip()
    except Exception as e:
        result_text = f"[STT 에러 발생] 음성 인식 중 문제가 발생했습니다. (상세: {e})"
    finally:
        if os.path.exists(filename):
            os.remove(filename)
            
    return result_text

# 텍스트 답변 생성 (LLM) - 무한 로딩 방지용 예외 처리 포함
def ask_gemini(messages, model_name, apikey, system_prompt):
    genai.configure(api_key=apikey)
    
    try:
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_prompt
        )
        
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
        return f"[답변 에러 발생] 제미나이가 답변을 생성하지 못했습니다. API 키나 네트워크를 확인해주세요. (상세: {e})"

# 텍스트 -> 음성 (TTS)
def TTS(response):
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
                <audio controls autoplay>
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
                """
            st.markdown(md, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"TTS 오류: {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

##### 2. 메인 웹 화면 구현 #####
def main():
    st.set_page_config(page_title="환장연애 - AI 연애 상담소", layout="wide")

    if "chats" not in st.session_state:
        st.session_state["chats"] = {}      
    if "messages" not in st.session_state:
        st.session_state["messages"] = {}   
    if "check_reset" not in st.session_state:
        st.session_state["check_reset"] = False
    if "last_audio_len" not in st.session_state:
        st.session_state["last_audio_len"] = 0
    if "prev_persona" not in st.session_state:
        st.session_state["prev_persona"] = ""

    # 배너 이미지 출력
    if os.path.exists("banner.png"):
        st.markdown(
            """
            <style>
            .banner-container {
                display: flex;
                justify-content: center;
                margin-bottom: 20px;
            }
            .banner-container img {
                width: 100%;
                max-height: 180px;
                object-fit: cover;
                border-radius: 12px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        
        with open("banner.png", "rb") as img_file:
            img_bytes = img_file.read()
            img_b64 = base64.b64encode(img_bytes).decode()
            st.markdown(f'<div class="banner-container"><img src="data:image/png;base64,{img_b64}"></div>', unsafe_allow_html=True)
    else:
        st.header("환장연애 EXChange - 연애 상담소")

    st.markdown("---")

    personas = {
        "🧊 냉정한 팩폭러": "너는 매우 냉정하고 객관적인 연애 상담사야. 사용자의 감정에 휘둘리지 말고, 상황을 냉철하게 분석해서 뼈를 때리는 팩트 폭력과 함께 현실적인 조언을 해줘. 말투는 차갑고 단호하게 해.",
        "🥰 무조건 내 편": "너는 무조건 사용자의 편을 들어주는 따뜻한 연애 상담사야. 사용자가 무슨 말을 하든 전적으로 공감해주고, 위로해주며, 필요하다면 상대방을 같이 욕해줘. 다정하고 따뜻한 말투를 사용해.",
        "👨‍👩‍👧 부모님의 마음": "너는 사용자를 진심으로 아끼고 사랑하는 엄마 혹은 아빠야. 자식이 연애 문제로 마음고생하는 걸 안타까워하면서도, 언제나 든든한 내 편이 되어주고 인생 선배로서 따뜻한 조언을 해줘. '우리 딸(혹은 아들) 속상했구나, 밥은 먹었어?' 같이 애정 넘치고 포근한 부모님의 말투를 사용해.",
        "✍️ 직접 성향 입력하기": "" 
    }

    with st.sidebar:
        gemini_api_key = st.text_input(label="Gemini API 키", placeholder="API 키를 입력하세요", type="password")
        st.markdown("---")
        
        st.subheader("👤 상담사 선택")
        selected_persona_title = st.radio("어떤 상담을 원하시나요?", list(personas.keys()), index=0)
        
        if st.session_state["prev_persona"] != selected_persona_title:
            st.session_state["prev_persona"] = selected_persona_title
            st.session_state["last_audio_len"] = 0

        if selected_persona_title == "✍️ 직접 성향 입력하기":
            custom_prompt = st.text_area(
                "상담사의 성격, 말투, 상황을 자세히 적어주세요.", 
                placeholder="예: 10년 지기 츤데레 찐친처럼 툴툴거리면서도 은근히 챙겨주는 말투로 팩폭 섞인 조언을 해줘."
            )
            selected_system_prompt = custom_prompt
        else:
            selected_system_prompt = personas[selected_persona_title]
        
        st.markdown("---")
        
        # 💡 [핵심 수정] 서버에서 확실히 지원하는 안정적인 공식 모델로 변경
        model_options = {
            "1.5 Flash (추천)": "gemini-1.5-flash",
            "1.5 Flash-8B": "gemini-1.5-flash-8b"
        }
        selected_model_ui = st.radio(label="Gemini 모델 선택", options=list(model_options.keys()), index=0)
        model = model_options[selected_model_ui]
        
        st.markdown("---")
        
        if st.button(label="대화 초기화 (현재 상담만)"):
            if selected_persona_title in st.session_state["chats"]:
                st.session_state["chats"][selected_persona_title] = []
            if selected_persona_title in st.session_state["messages"]:
                st.session_state["messages"][selected_persona_title] = []
            st.session_state["check_reset"] = True
            st.session_state["last_audio_len"] = 0
            st.rerun()

    if selected_persona_title not in st.session_state["chats"]:
        st.session_state["chats"][selected_persona_title] = []
    if selected_persona_title not in st.session_state["messages"]:
        st.session_state["messages"][selected_persona_title] = []

    col1, col2 = st.columns(2)
    
    user_question = "" 
    input_type = ""

    with col1:
        st.subheader(f"[{selected_persona_title}]에게 사연 말하기")
        
        audio = audiorecorder("🎤 클릭하여 사연 녹음하기", "🔴 녹음 중...")
        
        with st.form(key="text_input_form", clear_on_submit=True):
            text_input = st.text_input("💬 텍스트로 사연 적기", placeholder="연애 고민을 털어놓아 보세요.")
            submit_btn = st.form_submit_button(label="상담 요청")

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
                    
                    with st.spinner("사연을 듣는 중..."):
                        user_question = STT(audio, gemini_api_key, model)
                    input_type = "audio"

            if user_question:
                now = datetime.now().strftime("%H:%M")
                st.session_state["chats"][selected_persona_title].append(("user", now, user_question))
                if "[에러 발생]" not in user_question and "[STT 에러 발생]" not in user_question:
                    st.session_state["messages"][selected_persona_title].append({"role": "user", "content": user_question})

    with col2:
        st.subheader("상담사 답변")
        
        if user_question:
            if "[STT 에러 발생]" in user_question:
                response = "사연을 제대로 듣지 못했어요. 다시 말씀해주시겠어요?"
                st.session_state["chats"][selected_persona_title].append(("bot", datetime.now().strftime("%H:%M"), response))
            else:
                with st.spinner(f"{selected_persona_title}가 답변을 고민 중입니다..."):
                    response = ask_gemini(st.session_state["messages"][selected_persona_title], model, gemini_api_key, selected_system_prompt)
                
                if "[답변 에러 발생]" not in response:
                    st.session_state["messages"][selected_persona_title].append({"role": "model", "content": response})
                
                now = datetime.now().strftime("%H:%M")
                st.session_state["chats"][selected_persona_title].append(("bot", now, response))

        for sender, time, message in st.session_state["chats"][selected_persona_title]:
            if sender == "user":
                st.write(f'<div style="display:flex;align-items:center;"><div style="background-color:#FFD1DC;color:black;border-radius:12px;padding:8px 12px;margin-right:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
            else:
                st.write(f'<div style="display:flex;align-items:center;justify-content:flex-end;"><div style="background-color:#F0F0F0;color:black;border-radius:12px;padding:8px 12px;margin-left:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
            st.write("")
        
        if user_question and input_type == "audio":
            TTS(response)

if __name__ == "__main__":
    main()
