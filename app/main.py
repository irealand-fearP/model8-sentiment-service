"""
FastAPI 서버 본체.

구조:
  - lifespan: 서버가 켜질 때 모델을 1번만 로드한다.
  - GET  /health  : 서버/모델 상태 확인 (인증 불필요)
  - POST /predict : 감정 분석 (API Key 인증 필요, 비동기 추론)

비동기 추론(run_in_executor)을 쓰는 이유:
  모델 추론은 CPU를 오래 붙잡는 작업입니다. 그냥 호출하면 그동안
  서버 전체가 멈춰 다른 요청을 못 받습니다. 그래서 별도 스레드
  (ThreadPoolExecutor)에서 돌리고, 서버는 그 결과를 기다리는
  동안에도 다른 요청을 처리할 수 있게 합니다.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException

from app.auth import verify_api_key
from app.schemas import PredictRequest, PredictResponse
from app.model_service import load_model, predict

# 로드된 모델을 담아 둘 공간 (서버 전체가 공유)
ml_models = {}

# 추론을 돌릴 별도 스레드 풀
executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="sentiment")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시: 모델 로드
    print("모델을 로드합니다 ...")
    ml_models["model"] = load_model()
    print("모델 로드 완료")
    yield
    # 서버 종료 시: 정리
    ml_models.clear()


app = FastAPI(
    title="한국어 감정 분석 API",
    description="문장을 입력하면 긍정/부정/중립 감정을 예측합니다.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    """서버가 살아 있고 모델이 준비됐는지 확인한다(인증 불필요)."""
    return {
        "status": "healthy",
        "model_loaded": "model" in ml_models,
    }


@app.post("/predict", response_model=PredictResponse)
async def predict_endpoint(
    request: PredictRequest,
    user: str = Depends(verify_api_key),  # ← 이 한 줄이 인증을 적용한다
):
    """문장 하나의 감정을 분석해 반환한다.

    - 입력 검증: PredictRequest(Pydantic)가 자동 처리 → 잘못된 입력은 422
    - 인증:     Depends(verify_api_key) → 키 없으면 401
    - 추론:     run_in_executor로 별도 스레드에서 실행
    """
    model = ml_models.get("model")
    if model is None:
        # 모델이 아직 로드 전이면 503(일시적으로 서비스 불가)
        raise HTTPException(
            status_code=503,
            detail="모델이 아직 준비되지 않았습니다. 잠시 후 다시 시도하세요.",
        )

    try:
        loop = asyncio.get_event_loop()
        # predict(model, request.text)를 별도 스레드에서 실행하고 결과를 기다린다
        result = await loop.run_in_executor(
            executor, predict, model, request.text
        )
    except Exception as e:
        # 추론 자체에서 예기치 못한 오류가 나면 500
        raise HTTPException(status_code=500, detail=f"추론 중 오류가 발생했습니다: {e}")

    return PredictResponse(
        success=True,
        text=request.text,
        label=result["label"],
        confidence=result["confidence"],
    )
