from __future__ import annotations

import io
from pathlib import Path

from matplotlib import mathtext
from PIL import Image
from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QAction, QGuiApplication, QImage, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ocr.formula_engine import FormulaEngine
from utils.image_preprocess import (
    load_image,
    pil_to_qimage,
    preprocess_for_formula_ocr,
    qimage_to_pil,
)


class OCRWorker(QObject):
    """后台 OCR 线程任务。"""

    finished = Signal(str)
    failed = Signal(str)
    status = Signal(str)

    # 共享引擎：首次识别时初始化，后续复用，避免每次重复加载模型
    _shared_engine: FormulaEngine | None = None

    def __init__(self, image: Image.Image, backend: str = "auto") -> None:
        super().__init__()
        self.image = image
        self.backend = backend

    def run(self) -> None:
        try:
            if OCRWorker._shared_engine is None:
                self.status.emit("正在初始化 OCR 引擎（首次可能会下载模型，请稍候）...")
                OCRWorker._shared_engine = FormulaEngine(backend=self.backend)

            engine = OCRWorker._shared_engine
            if engine is None:
                raise RuntimeError("OCR 引擎初始化失败。")

            self.status.emit("正在识别公式...")
            processed = preprocess_for_formula_ocr(self.image)
            latex = engine.recognize_formula(processed)
            self.finished.emit(latex)
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("QiMathType - 公式图片转 LaTeX (MVP)")
        self.resize(1200, 800)
        self.setAcceptDrops(True)

        # OCR 后端类型。真正引擎实例由后台线程按需懒加载。
        self.ocr_backend = "auto"
        self.current_image: Image.Image | None = None

        self.ocr_thread: QThread | None = None
        self.ocr_worker: OCRWorker | None = None

        self._build_ui()
        self._bind_events()

    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)

        # 上半部分：左图右文本
        top_layout = QHBoxLayout()
        root_layout.addLayout(top_layout, stretch=3)

        self.image_group = QGroupBox("原图")
        image_layout = QVBoxLayout(self.image_group)
        self.image_label = QLabel("请打开图片 / 拖拽图片 / 粘贴图片")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setStyleSheet("border: 1px dashed #999; color: #666;")
        self.image_scroll = QScrollArea()
        self.image_scroll.setWidgetResizable(True)
        self.image_scroll.setWidget(self.image_label)
        image_layout.addWidget(self.image_scroll)
        top_layout.addWidget(self.image_group, stretch=1)

        self.latex_group = QGroupBox("识别结果（LaTeX）")
        latex_layout = QVBoxLayout(self.latex_group)
        self.latex_edit = QTextEdit()
        self.latex_edit.setPlaceholderText("识别结果会显示在这里。")
        latex_layout.addWidget(self.latex_edit)
        top_layout.addWidget(self.latex_group, stretch=1)

        # 下半部分：公式预览
        self.preview_group = QGroupBox("公式预览")
        preview_layout = QVBoxLayout(self.preview_group)
        self.preview_label = QLabel("暂无预览")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(160)
        self.preview_label.setStyleSheet("border: 1px solid #ddd; background: #fff;")
        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setWidget(self.preview_label)
        preview_layout.addWidget(self.preview_scroll)
        root_layout.addWidget(self.preview_group, stretch=2)

        # 底部按钮区
        btn_layout = QHBoxLayout()
        root_layout.addLayout(btn_layout)

        self.open_btn = QPushButton("打开图片")
        self.paste_btn = QPushButton("粘贴图片")
        self.recognize_btn = QPushButton("识别")
        self.copy_btn = QPushButton("复制 LaTeX")
        self.export_btn = QPushButton("导出 txt")
        self.clear_btn = QPushButton("清空")

        btn_layout.addWidget(self.open_btn)
        btn_layout.addWidget(self.paste_btn)
        btn_layout.addWidget(self.recognize_btn)
        btn_layout.addWidget(self.copy_btn)
        btn_layout.addWidget(self.export_btn)
        btn_layout.addWidget(self.clear_btn)

        # 菜单栏提供“打开图片”，满足桌面应用习惯
        file_menu = self.menuBar().addMenu("文件")
        self.open_action = QAction("打开图片", self)
        self.open_action.setShortcut(QKeySequence.Open)
        file_menu.addAction(self.open_action)

    def _bind_events(self) -> None:
        self.open_btn.clicked.connect(self.open_image_dialog)
        self.paste_btn.clicked.connect(self.paste_image_from_clipboard)
        self.recognize_btn.clicked.connect(self.start_recognition)
        self.copy_btn.clicked.connect(self.copy_latex)
        self.export_btn.clicked.connect(self.export_txt)
        self.clear_btn.clicked.connect(self.clear_all)
        self.open_action.triggered.connect(self.open_image_dialog)

        # 快捷键支持 Ctrl+V 粘贴图片
        self.paste_shortcut = QShortcut(QKeySequence.Paste, self)
        self.paste_shortcut.activated.connect(self.paste_image_from_clipboard)

        # 文本变化时实时刷新预览
        self.latex_edit.textChanged.connect(self.refresh_preview)

    def open_image_dialog(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图片",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp);;All Files (*)",
        )
        if not file_path:
            return
        self._load_image_from_path(file_path)

    def _load_image_from_path(self, file_path: str) -> None:
        try:
            image = load_image(file_path)
            self._set_current_image(image)
        except Exception as exc:
            QMessageBox.critical(self, "加载失败", f"无法打开图片：\n{exc}")

    def _set_current_image(self, image: Image.Image) -> None:
        self.current_image = image
        qimage = pil_to_qimage(image)
        pixmap = QPixmap.fromImage(qimage)
        self.image_label.setPixmap(pixmap)
        self.image_label.setAlignment(Qt.AlignCenter)

    def paste_image_from_clipboard(self) -> None:
        clipboard = QGuiApplication.clipboard()
        mime = clipboard.mimeData()

        # 优先处理真正的图片数据
        if mime is not None and mime.hasImage():
            qimage = clipboard.image()
            if not qimage.isNull():
                image = qimage_to_pil(qimage)
                self._set_current_image(image)
                return

        # 其次处理剪贴板中的本地文件 URL
        if mime is not None and mime.hasUrls():
            for url in mime.urls():
                if url.isLocalFile():
                    path = url.toLocalFile()
                    if self._is_image_file(path):
                        self._load_image_from_path(path)
                        return

        QMessageBox.information(self, "提示", "剪贴板中没有可用图片。")

    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        mime = event.mimeData()
        if mime.hasImage():
            event.acceptProposedAction()
            return

        if mime.hasUrls():
            for url in mime.urls():
                if url.isLocalFile() and self._is_image_file(url.toLocalFile()):
                    event.acceptProposedAction()
                    return

        event.ignore()

    def dropEvent(self, event) -> None:  # type: ignore[override]
        mime = event.mimeData()
        if mime.hasUrls():
            for url in mime.urls():
                if url.isLocalFile() and self._is_image_file(url.toLocalFile()):
                    self._load_image_from_path(url.toLocalFile())
                    event.acceptProposedAction()
                    return

        if mime.hasImage():
            qimage = event.mimeData().imageData()
            if isinstance(qimage, QImage):
                self._set_current_image(qimage_to_pil(qimage))
                event.acceptProposedAction()
                return
            if hasattr(qimage, "toImage"):
                self._set_current_image(qimage_to_pil(qimage.toImage()))
                event.acceptProposedAction()
                return

        event.ignore()

    def start_recognition(self) -> None:
        if self.current_image is None:
            QMessageBox.warning(self, "提示", "请先加载图片。")
            return

        if self.ocr_thread is not None and self.ocr_thread.isRunning():
            QMessageBox.information(self, "提示", "识别正在进行中，请稍候。")
            return

        self.recognize_btn.setEnabled(False)
        self.recognize_btn.setText("识别中（首次会初始化模型）...")

        self.ocr_thread = QThread(self)
        self.ocr_worker = OCRWorker(self.current_image.copy(), backend=self.ocr_backend)
        self.ocr_worker.moveToThread(self.ocr_thread)

        self.ocr_thread.started.connect(self.ocr_worker.run)
        self.ocr_worker.finished.connect(self._on_ocr_finished)
        self.ocr_worker.failed.connect(self._on_ocr_failed)
        self.ocr_worker.status.connect(self._on_ocr_status)

        # 线程结束后清理资源，避免多次识别造成对象泄漏
        self.ocr_worker.finished.connect(self._cleanup_ocr_thread)
        self.ocr_worker.failed.connect(self._cleanup_ocr_thread)

        self.ocr_thread.start()

    def _on_ocr_finished(self, latex: str) -> None:
        self.latex_edit.setPlainText(latex)
        self.recognize_btn.setEnabled(True)
        self.recognize_btn.setText("识别")

    def _on_ocr_failed(self, message: str) -> None:
        self.recognize_btn.setEnabled(True)
        self.recognize_btn.setText("识别")
        QMessageBox.critical(self, "识别失败", f"识别过程出错：\n{message}")

    def _on_ocr_status(self, message: str) -> None:
        # 将阶段性状态反馈到按钮文案，给用户明确进度感知
        self.recognize_btn.setText(message)

    def _cleanup_ocr_thread(self) -> None:
        if self.ocr_thread is not None:
            self.ocr_thread.quit()
            self.ocr_thread.wait()
            self.ocr_thread.deleteLater()
            self.ocr_thread = None

        if self.ocr_worker is not None:
            self.ocr_worker.deleteLater()
            self.ocr_worker = None

    def refresh_preview(self) -> None:
        latex = self.latex_edit.toPlainText().strip()
        if not latex:
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText("暂无预览")
            return

        try:
            rendered = latex
            if not (rendered.startswith("$") and rendered.endswith("$")):
                rendered = f"${rendered}$"

            buffer = io.BytesIO()
            mathtext.math_to_image(rendered, buffer, dpi=220, format="png")
            pixmap = QPixmap()
            pixmap.loadFromData(buffer.getvalue(), "PNG")

            self.preview_label.setText("")
            self.preview_label.setPixmap(pixmap)
            self.preview_label.setAlignment(Qt.AlignCenter)
        except Exception as exc:
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText(f"预览失败，请检查 LaTeX 语法。\n{exc}")

    def copy_latex(self) -> None:
        latex = self.latex_edit.toPlainText().strip()
        if not latex:
            QMessageBox.information(self, "提示", "当前没有可复制的 LaTeX。")
            return

        QGuiApplication.clipboard().setText(latex)
        QMessageBox.information(self, "成功", "LaTeX 已复制到剪贴板。")

    def export_txt(self) -> None:
        latex = self.latex_edit.toPlainText().strip()
        if not latex:
            QMessageBox.information(self, "提示", "当前没有可导出的 LaTeX。")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出为 txt",
            "formula.txt",
            "Text Files (*.txt)",
        )
        if not save_path:
            return

        try:
            Path(save_path).write_text(latex, encoding="utf-8")
            QMessageBox.information(self, "成功", f"已导出：\n{save_path}")
        except Exception as exc:
            QMessageBox.critical(self, "导出失败", f"写入文件失败：\n{exc}")

    def clear_all(self) -> None:
        self.current_image = None
        self.image_label.setPixmap(QPixmap())
        self.image_label.setText("请打开图片 / 拖拽图片 / 粘贴图片")
        self.latex_edit.clear()
        self.preview_label.setPixmap(QPixmap())
        self.preview_label.setText("暂无预览")

    def closeEvent(self, event) -> None:  # type: ignore[override]
        # 窗口关闭时确保后台线程安全退出
        if self.ocr_thread is not None and self.ocr_thread.isRunning():
            self.ocr_thread.quit()
            self.ocr_thread.wait()
        super().closeEvent(event)

    @staticmethod
    def _is_image_file(path: str) -> bool:
        suffix = Path(path).suffix.lower()
        return suffix in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
