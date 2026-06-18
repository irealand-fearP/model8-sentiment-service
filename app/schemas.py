"""
입력/출력 스키마 정의 (Pydantic).

Pydantic(파이단틱)은 "들어온 데이터가 약속한 형식이 맞는지"를
자동으로 검사해 주는 도구입니다. 형식이 틀리면 FastAPI가
자동으로 422 에러와 함께 어디가 잘못됐는지 알려줍니다.
"""
from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    """추론 요청 입력: 분석할 한국어 문장 하나."""

    # text: 필수 필드(...). 빈 문자열은 막고(min_length=1),
    #        너무 긴 입력도 막는다(max_length=1000).
    text: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="감정을 분석할 한국어 문장",
    )

    # Swagger UI(API 문서 화면)에 보여줄 입력 예시
    model_config = {
        "json_schema_extra": {
            "example": {"text": "오늘 주가가 크게 올라서 기분이 좋습니다."}
        }
    }


class PredictResponse(BaseModel):
    """추론 응답 출력."""

    success: bool          # 처리 성공 여부
    text: str              # 분석에 사용한 원본 문장
    label: str             # 예측된 감정 라벨 (예: positive/negative/neutral)
    confidence: float      # 모델이 그 라벨을 얼마나 확신하는지 (0~1)
