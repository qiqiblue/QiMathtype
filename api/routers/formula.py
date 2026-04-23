from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from PIL import UnidentifiedImageError

from api.schemas import BackendType, HealthResponse, RecognizeResponse
from services.formula_service import FormulaRecognitionService

router = APIRouter(prefix="/api/v1", tags=["formula"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """健康检查接口。"""
    return HealthResponse()


@router.post("/formula/recognize", response_model=RecognizeResponse)
def recognize_formula(
    file: UploadFile = File(..., description="待识别的公式图片"),
    backend: BackendType = BackendType.AUTO,
) -> RecognizeResponse:
    """
    上传图片并返回 LaTeX。
    - 输入：multipart/form-data，字段名为 file
    - 输出：识别结果与引擎信息
    """
    content_type = (file.content_type or "").lower()
    if content_type and not content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"仅支持图片文件，当前类型：{content_type}",
        )

    image_bytes = file.file.read()
    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="上传文件为空。",
        )

    try:
        result = FormulaRecognitionService.recognize_bytes(
            image_bytes=image_bytes,
            backend=backend.value,
        )
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无法解析图片：{exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"识别失败：{exc}",
        ) from exc
    finally:
        file.file.close()

    return RecognizeResponse(
        latex=result.latex,
        backend=backend,
        engine_name=result.engine.name,
        engine_ready=result.engine.ready,
        engine_message=result.engine.message,
    )
