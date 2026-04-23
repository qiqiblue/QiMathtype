# Web 开发文档（MVP）

## 1. 启动

Web MVP 与 API 共用同一个 FastAPI 进程，启动命令：

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

访问：

- Web 页面：`http://127.0.0.1:8000/`
- API 文档：`http://127.0.0.1:8000/docs`

## 2. 功能

- 上传图片（点击选择）
- 拖拽图片上传
- 调用 API：`POST /api/v1/formula/recognize`
- 展示 LaTeX 结果
- 复制 LaTeX 到剪贴板

## 3. 文件结构

```text
web/
├─ templates/
│  └─ index.html
└─ static/
   ├─ app.js
   └─ style.css
```

## 4. 联调说明

- 前端和后端同域运行，不需要额外代理
- 默认调用 `backend=auto`
- 若 OCR 引擎未就绪，页面会显示引擎状态提示
