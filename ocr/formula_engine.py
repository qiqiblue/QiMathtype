from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from PIL import Image


@dataclass
class EngineInfo:
    """当前 OCR 后端信息。"""

    name: str
    ready: bool
    message: str


class FormulaEngine:
    """
    公式 OCR 引擎封装。
    优先顺序：
    1. pix2tex
    2. pix2text
    """

    def __init__(self, backend: str = "auto") -> None:
        self.backend = backend
        self.model: Any = None
        self.engine_info = self._init_engine(backend)

    def _init_engine(self, backend: str) -> EngineInfo:
        if backend in ("auto", "pix2tex"):
            info = self._init_pix2tex()
            if info.ready or backend == "pix2tex":
                return info

        if backend in ("auto", "pix2text"):
            info = self._init_pix2text()
            return info

        return EngineInfo(
            name="none",
            ready=False,
            message="未识别的后端配置，请使用 auto / pix2tex / pix2text。",
        )

    def _init_pix2tex(self) -> EngineInfo:
        try:
            # pix2tex 官方常见调用入口
            from pix2tex.cli import LatexOCR

            self.model = LatexOCR()
            return EngineInfo(
                name="pix2tex",
                ready=True,
                message="pix2tex 初始化成功。",
            )
        except Exception as exc:
            return EngineInfo(
                name="pix2tex",
                ready=False,
                message=f"pix2tex 初始化失败：{exc}",
            )

    def _init_pix2text(self) -> EngineInfo:
        try:
            # pix2text 常见入口
            from pix2text import Pix2Text

            # Pix2Text 的配置接口在不同版本有差异，这里做兼容判断
            if hasattr(Pix2Text, "from_config"):
                self.model = Pix2Text.from_config()
            else:
                self.model = Pix2Text()

            return EngineInfo(
                name="pix2text",
                ready=True,
                message="pix2text 初始化成功。",
            )
        except Exception as exc:
            return EngineInfo(
                name="pix2text",
                ready=False,
                message=f"pix2text 初始化失败：{exc}",
            )

    def recognize_formula(self, image: Image.Image) -> str:
        """
        对输入图片执行公式识别，返回 LaTeX。
        """
        if not self.engine_info.ready or self.model is None:
            return (
                r"\text{OCR 引擎未就绪：请安装 pix2tex 或 pix2text。}"
                + "\n"
                + self.engine_info.message
            )

        if self.engine_info.name == "pix2tex":
            return self._recognize_with_pix2tex(image)

        if self.engine_info.name == "pix2text":
            return self._recognize_with_pix2text(image)

        return r"\text{暂不支持当前 OCR 后端。}"

    def _recognize_with_pix2tex(self, image: Image.Image) -> str:
        result = self.model(image)
        if isinstance(result, str):
            return result.strip()
        return str(result).strip()

    def _recognize_with_pix2text(self, image: Image.Image) -> str:
        """
        兼容不同 pix2text 版本的识别函数。
        """
        model = self.model
        result: Any = None

        if hasattr(model, "recognize_formula"):
            result = model.recognize_formula(image)
        elif hasattr(model, "recognize"):
            result = model.recognize(image)
        elif hasattr(model, "__call__"):
            result = model(image)
        else:
            raise RuntimeError("pix2text 模型不包含可调用的识别方法。")

        # 常见返回类型兼容处理
        if isinstance(result, str):
            return result.strip()

        if isinstance(result, dict):
            for key in ("latex", "text", "result"):
                if key in result:
                    return str(result[key]).strip()
            return str(result).strip()

        if isinstance(result, list):
            if not result:
                return ""
            first = result[0]
            if isinstance(first, dict):
                for key in ("latex", "text", "result"):
                    if key in first:
                        return str(first[key]).strip()
            return str(first).strip()

        return str(result).strip()
