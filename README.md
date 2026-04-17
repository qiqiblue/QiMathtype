# QiMathType MVP

一个基于 `PySide6` 的桌面工具：识别图片中的数学公式并转换为 LaTeX。

## 功能（MVP）

- 打开本地图片识别公式
- 支持拖拽图片到窗口
- 支持粘贴剪贴板图片（`Ctrl+V`）
- 左侧显示原图，右侧显示 LaTeX
- 下方提供公式预览区域
- 提供按钮：`识别`、`复制 LaTeX`、`导出 txt`、`清空`
- OCR 在后台线程运行，避免界面卡顿
- 预留并封装 `pix2tex / pix2text` 后端接口

## 快速开始

```bash
pip install -r requirements.txt
python main.py
```

> 说明：`pix2tex` 和 `pix2text` 模型依赖较重，首次安装可能较慢。  
> 若未安装 OCR 后端，程序仍可启动，但识别会返回引擎未就绪提示。

## 项目结构

```text
QiMathtype/
├─ main.py
├─ requirements.txt
├─ README.md
├─ ocr/
│  └─ formula_engine.py
├─ ui/
│  └─ main_window.py
├─ utils/
│  └─ image_preprocess.py
└─ docs/
   └─ development.md
```

## 开发文档

详见 [docs/development.md](docs/development.md)。
