"""
모델 로드와 추론 함수.

- load_model(): 감정분석 모델을 메모리에 올린다(서버 시작 때 1번).
- predict(): 문장 하나를 받아 감정 라벨과 확신도를 돌려준다.

사용 모델: snunlp/KR-FinBert-SC
  한국어 금융/일반 문장의 감정을 positive/negative/neutral로 분류합니다.
"""
from transformers import pipeline

# 사용할 사전학습 모델 이름 (Hugging Face Hub 기준)
MODEL_NAME = "snunlp/KR-FinBert-SC"


def load_model():
    """감정분석 파이프라인을 만들어 반환한다.

    pipeline()은 토크나이저+모델+후처리를 한 번에 묶어 주는
    transformers의 편의 도구입니다. 처음 호출할 때 모델을
    내려받으므로 시간이 걸릴 수 있습니다(이후에는 캐시 사용).
    """
    return pipeline("text-classification", model=MODEL_NAME)


def predict(model, text: str) -> dict:
    """문장 하나를 추론해 결과를 dict로 반환한다.

    Args:
        model: load_model()이 만든 파이프라인
        text:  분석할 문장

    Returns:
        {"label": 감정라벨, "confidence": 확신도(0~1)}
    """
    # 파이프라인은 [{'label': ..., 'score': ...}] 형태로 돌려준다.
    result = model(text)[0]
    return {
        "label": result["label"],
        "confidence": float(result["score"]),
    }
