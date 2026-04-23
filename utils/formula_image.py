from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageOps


def load_image(image_path: str | Path) -> Image.Image:
    """从本地路径加载图片并统一为 RGB。"""
    path = Path(image_path)
    image = Image.open(path)
    return image.convert("RGB")


def load_image_from_bytes(image_bytes: bytes) -> Image.Image:
    """从二进制字节加载图片并统一为 RGB。"""
    with io.BytesIO(image_bytes) as stream:
        image = Image.open(stream)
        return image.convert("RGB")


def preprocess_for_formula_ocr(image: Image.Image) -> Image.Image:
    """
    公式 OCR 轻量预处理：
    1. 转灰度
    2. 轻微自动对比度增强
    3. 转回 RGB
    """
    gray = image.convert("L")
    enhanced = ImageOps.autocontrast(gray, cutoff=1)
    return enhanced.convert("RGB")
