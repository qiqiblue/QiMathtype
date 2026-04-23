from __future__ import annotations

from dataclasses import dataclass
from threading import Lock

from PIL import Image

from ocr.formula_engine import FormulaEngine
from utils.formula_image import load_image_from_bytes, preprocess_for_formula_ocr


@dataclass(frozen=True)
class EngineState:
    """OCR 引擎状态快照。"""

    name: str
    ready: bool
    message: str


@dataclass(frozen=True)
class RecognitionResult:
    """公式识别结果。"""

    latex: str
    engine: EngineState


class FormulaRecognitionService:
    """
    公式识别共享服务层。
    - GUI 与后续 API/Web 共用
    - 内置引擎单例复用，避免重复加载模型
    """

    _engine: FormulaEngine | None = None
    _backend: str | None = None
    _lock = Lock()

    @classmethod
    def ensure_engine(cls, backend: str = "auto") -> EngineState:
        engine = cls._get_or_create_engine(backend)
        info = engine.engine_info
        return EngineState(name=info.name, ready=info.ready, message=info.message)

    @classmethod
    def recognize_image(cls, image: Image.Image, backend: str = "auto") -> RecognitionResult:
        engine = cls._get_or_create_engine(backend)
        processed = preprocess_for_formula_ocr(image)
        latex = engine.recognize_formula(processed)
        info = engine.engine_info
        return RecognitionResult(
            latex=latex,
            engine=EngineState(name=info.name, ready=info.ready, message=info.message),
        )

    @classmethod
    def recognize_bytes(cls, image_bytes: bytes, backend: str = "auto") -> RecognitionResult:
        image = load_image_from_bytes(image_bytes)
        return cls.recognize_image(image, backend=backend)

    @classmethod
    def reset_engine(cls) -> None:
        """重置缓存引擎，便于调试或切换后端。"""
        with cls._lock:
            cls._engine = None
            cls._backend = None

    @classmethod
    def _get_or_create_engine(cls, backend: str) -> FormulaEngine:
        if cls._engine is not None and cls._backend == backend:
            return cls._engine

        with cls._lock:
            if cls._engine is None or cls._backend != backend:
                cls._engine = FormulaEngine(backend=backend)
                cls._backend = backend
            return cls._engine
