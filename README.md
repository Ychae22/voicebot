# 💬 환장연애 (EXChange) - AI 연애 상담소

> **"속 시원한 팩폭부터 무조건적인 위로까지, 원하는 페르소나를 골라 듣는 맞춤형 음성 AI 연애 상담 서비스"**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://voicebot-4wgnzlwiq6hcmh3wmrplsd.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-3.1_Flash_Lite-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)

![Banner](banner.png)

---

## 📌 서비스 소개

**환장연애 AI 연애 상담소**는 음성 또는 텍스트로 연애 고민을 털어놓으면, 사용자가 선택한 성향(페르소나)의 상담사가 실시간으로 솔루션을 제공하는 음성 챗봇 애플리케이션입니다.

- 🎤 **음성 & 텍스트 지원**: 마이크로 사연을 직접 말하거나 텍스트로 적어 편하게 소통할 수 있습니다.
- 🤖 **Google Gemini 멀티모달 STT**: 녹음된 오디오를 Gemini 모델이 직접 분석하여 정확한 한국어 텍스트로 변환합니다.
- 🗣️ **gTTS 음성 답변**: 음성으로 사연을 보내면 상담사의 답변도 음성(TTS)으로 들려줍니다.
- 🎭 **4가지 맞춤 페르소나**: 원하는 상담 스타일에 맞춰 현실적인 조언과 따뜻한 위로를 받을 수 있습니다.

---

## ✨ 주요 기능

### 1. 🎭 4가지 맞춤형 상담사 페르소나
- **🧊 냉정한 팩폭러**: 객관적이고 냉철한 상황 분석, 뼈 때리는 팩트 폭력과 현실적인 조언
- **🥰 무조건 내 편**: 사용자의 말에 전적으로 공감하고 함께 분노해주며 든든한 위로 제공
- **👨‍👩‍👧 부모님의 마음**: 자식을 아끼는 부모님의 포근하고 애정 어린 인생 선배의 조언
- **✍️ 직접 성향 입력하기**: 사용자가 원하는 말투(예: 10년 지기 츤데레 찐친 등)를 자유롭게 커스텀 프롬프트로 지정

### 2. 🎙️ 멀티모달 음성 입출력 파이프라인
- **STT (Speech-to-Text)**: `streamlit-audiorecorder`로 녹음한 음성을 Google Gemini 멀티모달 API에 전달하여 텍스트로 인식
- **LLM 대화 생성**: 이전 대화 맥락(History)과 System Prompt(페르소나)를 결합하여 맞춤 답변 도출
- **TTS (Text-to-Speech)**: `gTTS`를 사용해 상담사의 답변을 음성 MP3로 실시간 렌더링 및 자동 재생

### 3. 💬 독립적인 세션 히스토리 관리
- 상담사 페르소나마다 대화 기록이 분리되어 저장되므로, 여러 상담사와 독립적으로 연속 대화가 가능합니다.
- 사이드바의 **[대화 초기화]** 버튼으로 현재 상담 중인 세션만 안전하게 리셋할 수 있습니다.

---

## 🛠️ 기술 스택 (Tech Stack)

| 구분 | 기술 / 라이브러리 | 설명 |
| :--- | :--- | :--- |
| **Frontend / Web** | [Streamlit](https://streamlit.io/) | 반응형 웹 UI 및 인터랙티브 인터페이스 구축 |
| **Audio Recorder** | `streamlit-audiorecorder` | 브라우저 기반 실시간 마이크 음성 녹음 |
| **STT & LLM** | Google Gemini API (`google-generativeai`) | `gemini-3.1-flash-lite` 모델을 활용한 음성 인식 및 페르소나 상담 |
| **TTS** | [gTTS (Google Text-to-Speech)](https://github.com/pndurette/gTTS) | 답변 텍스트의 한국어 음성 합성 및 재생 |
| **System Dependency** | `ffmpeg` | 오디오 파일 포맷 인코딩/디코딩 처리 |

---

## 📂 프로젝트 구조

```
voicebot/
├── banner.png           # 앱 상단 대표 배너 이미지
├── voicebot.py          # 메인 Streamlit 애플리케이션 소스 코드
├── requirements.txt     # Python 패키지 의존성 목록
├── packages.txt         # Streamlit Cloud 시스템 패키지 (ffmpeg)
└── README.md            # 프로젝트 소개 및 안내 문서
```

---

## 🚀 로컬 실행 방법 (Getting Started)

### 1. 레포지토리 클론
```bash
git clone https://github.com/Ychae22/voicebot.git
cd voicebot
```

### 2. 필수 패키지 설치
```bash
pip install -r requirements.txt
```

> **⚠️ 시스템 의존성(FFmpeg) 안내**:
> 오디오 처리를 위해 시스템에 `ffmpeg`가 설치되어 있어야 합니다.
> - **Ubuntu/Debian**: `sudo apt install ffmpeg`
> - **macOS**: `brew install ffmpeg`
> - **Windows**: `winget install Gyan.FFmpeg` 또는 공식 홈페이지에서 설치 후 환경변수 PATH 추가

### 3. Streamlit 앱 실행
```bash
streamlit run voicebot.py
```

### 4. API 키 발급 및 입력
1. [Google AI Studio](https://aistudio.google.com/app/apikey)에서 Gemini API 키를 발급받습니다.
2. 실행된 브라우저 좌측 사이드바의 **[Gemini API 키]** 입력란에 키를 입력합니다.
3. 원하는 상담사 성향을 선택하고 사연을 녹음하거나 입력하여 상담을 시작하세요!

---

## 🌐 배포 링크
- **Streamlit Community Cloud**: [https://voicebot-4wgnzlwiq6hcmh3wmrplsd.streamlit.app/](https://voicebot-4wgnzlwiq6hcmh3wmrplsd.streamlit.app/)
