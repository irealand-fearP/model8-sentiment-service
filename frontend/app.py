"""
Streamlit 프론트엔드.

비개발자도 쓸 수 있는 웹 화면입니다.
사용자가 문장을 입력하면 -> 우리 FastAPI 서버에 요청 -> 결과를 보여줍니다.

실행 방법 (서버가 먼저 떠 있어야 합니다):
  streamlit run frontend/app.py
"""
import requests
import streamlit as st

# 우리가 띄운 FastAPI 서버 주소
API_URL = "http://localhost:8000"

st.set_page_config(page_title="한국어 감정 분석", page_icon="🙂")
st.title("🙂 한국어 감정 분석 서비스")
st.caption("문장을 입력하면 긍정/부정/중립을 예측합니다. (모델: snunlp/KR-FinBert-SC)")

# 사이드바: API Key 입력
with st.sidebar:
    st.header("설정")
    api_key = st.text_input(
        "API Key",
        value="test-key-001",
        type="password",
        help="서버에 등록된 키를 입력하세요. (예: test-key-001)",
    )
    st.markdown("---")
    # 서버 상태 확인 버튼
    if st.button("서버 상태 확인"):
        try:
            health = requests.get(f"{API_URL}/health", timeout=5).json()
            if health.get("model_loaded"):
                st.success("서버 정상 · 모델 로드됨")
            else:
                st.warning("서버는 살아 있으나 모델 로딩 중입니다.")
        except Exception:
            st.error("서버에 연결할 수 없습니다. 서버를 먼저 실행하세요.")

# 본문: 문장 입력
text = st.text_area(
    "분석할 문장",
    value="오늘 주가가 크게 올라서 기분이 좋습니다.",
    height=120,
)

if st.button("감정 분석하기", type="primary"):
    if not text.strip():
        st.warning("문장을 입력해 주세요.")
    else:
        try:
            response = requests.post(
                f"{API_URL}/predict",
                json={"text": text},
                headers={"X-API-Key": api_key},
                timeout=30,
            )
        except Exception as e:
            st.error(f"요청 실패: 서버가 실행 중인지 확인하세요. ({e})")
        else:
            if response.status_code == 200:
                data = response.json()
                label = data["label"]
                confidence = data["confidence"]
                st.subheader("분석 결과")
                st.metric(label="예측 감정", value=label)
                st.write(f"확신도: **{confidence:.1%}**")
                st.progress(min(max(confidence, 0.0), 1.0))
            elif response.status_code == 401:
                st.error("인증 실패(401): API Key가 없거나 올바르지 않습니다.")
            elif response.status_code == 422:
                st.error("입력 오류(422): 문장 형식이 올바르지 않습니다.")
            else:
                st.error(f"오류({response.status_code}): {response.text}")
