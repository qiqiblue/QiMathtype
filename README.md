# QiMathType

数学公式图片转 LaTeX 的多形态 MVP 项目，支持：

- GUI 桌面版（PySide6）
- API 服务版（FastAPI）
- Web 页面版（原生 HTML/CSS/JS，调用同一套 API）

项目目标是复用同一套 OCR 能力，避免 GUI、Web、API 重复实现识别逻辑。

## 1. 功能概览

### 1.1 GUI 桌面版

- 打开本地图片
- 拖拽图片
- 粘贴剪贴板图片（`Ctrl + V`）
- 左侧原图、右侧 LaTeX 结果、下方公式预览
- 按钮功能：`识别`、`复制 LaTeX`、`导出 txt`、`清空`
- OCR 在后台线程执行，避免界面卡顿

### 1.2 API 版

- `GET /api/v1/health`：健康检查
- `POST /api/v1/formula/recognize`：上传图片并返回 LaTeX
- Swagger 文档：`/docs`

### 1.3 Web 版

- 上传/拖拽图片
- 调用 `POST /api/v1/formula/recognize`
- 展示 LaTeX
- 一键复制结果

## 2. 架构说明

核心复用路径：

- `ocr/formula_engine.py`：OCR 引擎封装（pix2tex / pix2text）
- `services/formula_service.py`：共享识别服务层（GUI/API 共用）
- `ui/`：GUI 交互层
- `api/`：HTTP 接口层
- `web/`：前端页面层（通过 API 调用能力）

这样可以保证三端隔离、识别逻辑单点维护。

## 3. 项目结构

```text
QiMathtype/
├─ main.py
├─ requirements.txt
├─ README.md
├─ api/
│  ├─ main.py
│  ├─ schemas.py
│  └─ routers/
│     └─ formula.py
├─ docs/
│  ├─ development.md
│  ├─ api.md
│  └─ web.md
├─ ocr/
│  └─ formula_engine.py
├─ services/
│  └─ formula_service.py
├─ ui/
│  └─ main_window.py
├─ utils/
│  ├─ formula_image.py
│  └─ image_preprocess.py
└─ web/
   ├─ templates/
   │  └─ index.html
   └─ static/
      ├─ app.js
      └─ style.css
```

## 4. 环境要求

- 建议 Python：`3.10+`（推荐 `3.12`）
- 系统：Windows / Linux / macOS
- 首次使用 OCR 可能下载模型权重，耗时取决于网络

> 注意：Python 3.9 下依赖兼容更复杂，若要稳定使用 `pix2tex`，强烈建议升级到 3.10+。

## 5. 安装依赖

```bash
pip install -r requirements.txt
```

## 6. 运行方式

### 6.1 启动 GUI 桌面版

```bash
python main.py
```

### 6.2 启动 API + Web

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

启动后地址：

- Web 页面：`http://127.0.0.1:8000/`
- API 文档：`http://127.0.0.1:8000/docs`
- 健康检查：`http://127.0.0.1:8000/api/v1/health`
- API 信息：`http://127.0.0.1:8000/api-info`

## 7. API 快速测试

### 7.1 健康检查

```bash
curl http://127.0.0.1:8000/api/v1/health
```

### 7.2 识别接口

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/formula/recognize?backend=auto" \
  -F "file=@./demo.png"
```

返回字段示例：

- `latex`
- `backend`
- `engine_name`
- `engine_ready`
- `engine_message`

## 8. 常见问题（FAQ）

### 8.1 `/openapi.json` 报错 `_SpecialForm has no attribute replace`

通常是 `FastAPI + Pydantic + Python` 版本组合不兼容导致。  
优先使用 Python 3.10+，并重装依赖：

```bash
pip install -r requirements.txt
```

### 8.2 `pix2tex 初始化失败：cannot import name 'ValidationInfo'`

通常是当前环境中的 `pydantic` 版本与 `pix2tex` 不匹配。  
建议新建 Python 3.12 虚拟环境后重新安装。

### 8.3 首次识别很慢或像“卡住”

首次识别可能会下载和加载模型权重，属正常现象。  
可观察控制台日志与按钮状态提示。

## 9. 开发文档

- [docs/development.md](docs/development.md)
- [docs/api.md](docs/api.md)
- [docs/web.md](docs/web.md)

## 10. 版本目标

当前是 MVP，聚焦本地识别闭环与多端能力验证。  
暂不包含登录、数据库、云部署、多租户等复杂功能。
