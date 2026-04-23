from __future__ import annotations

import io

from PIL import Image
from PySide6.QtCore import QBuffer, QByteArray, QIODevice
from PySide6.QtGui import QImage

from utils.formula_image import load_image, preprocess_for_formula_ocr


def qimage_to_pil(qimage: QImage) -> Image.Image:
    """将 QImage 转为 PIL Image。"""
    # 统一为 RGBA，保证各平台格式一致
    rgba_image = qimage.convertToFormat(QImage.Format_RGBA8888)
    width = rgba_image.width()
    height = rgba_image.height()
    ptr = rgba_image.bits()
    if hasattr(ptr, "setsize"):
        ptr.setsize(rgba_image.sizeInBytes())
    raw = bytes(ptr)
    return Image.frombytes("RGBA", (width, height), raw, "raw", "RGBA").convert("RGB")


def pil_to_qimage(image: Image.Image) -> QImage:
    """将 PIL Image 转为 QImage。"""
    rgb = image.convert("RGB")
    raw = rgb.tobytes("raw", "RGB")
    qimage = QImage(raw, rgb.width, rgb.height, rgb.width * 3, QImage.Format_RGB888)
    # copy() 用于脱离底层内存引用，避免显示时出现悬空指针
    return qimage.copy()


def qimage_from_clipboard_data(image_data: QByteArray) -> QImage:
    """将剪贴板字节数据解码为 QImage。"""
    buffer = QBuffer()
    buffer.setData(image_data)
    buffer.open(QIODevice.ReadOnly)
    image = QImage()
    image.loadFromData(buffer.data())
    return image


def pil_image_to_png_bytes(image: Image.Image) -> bytes:
    """将 PIL 图片编码为 PNG 字节，用于界面显示或导出。"""
    with io.BytesIO() as output:
        image.save(output, format="PNG")
        return output.getvalue()
