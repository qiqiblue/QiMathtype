from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class BackendType(str, Enum):
    """OCR 后端类型。"""

    AUTO = "auto"
    PIX2TEX = "pix2tex"
    PIX2TEXT = "pix2text"


class HealthResponse(BaseModel):
    """健康检查响应。"""

    status: str = "ok"
    service: str = Field(default="qimathtype-api")


class RecognizeResponse(BaseModel):
    """公式识别响应。"""

    latex: str = Field(description="识别出的 LaTeX 字符串")
    backend: BackendType = Field(description="本次请求指定的后端")
    engine_name: str = Field(description="实际使用的 OCR 引擎名称")
    engine_ready: bool = Field(description="引擎是否就绪")
    engine_message: str = Field(description="引擎状态信息")
