# API 开发文档（MVP）

## 1. 启动方式

在项目根目录执行：

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

启动后可访问：

- Web 页面：`http://127.0.0.1:8000/`
- Swagger 文档：`http://127.0.0.1:8000/docs`
- 健康检查：`http://127.0.0.1:8000/api/v1/health`
- API 信息：`http://127.0.0.1:8000/api-info`

## 2. 接口说明

### 2.1 健康检查

- 方法：`GET`
- 路径：`/api/v1/health`
- 作用：检查服务是否启动成功

示例响应：

```json
{
  "status": "ok",
  "service": "qimathtype-api"
}
```

### 2.2 公式识别

- 方法：`POST`
- 路径：`/api/v1/formula/recognize`
- Content-Type：`multipart/form-data`
- 表单字段：
  - `file`: 图片文件（必填）
- Query 参数：
  - `backend`: `auto | pix2tex | pix2text`（可选，默认 `auto`）

示例（curl）：

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/formula/recognize?backend=auto" \
  -F "file=@./demo.png"
```

示例响应：

```json
{
  "latex": "\\frac{a}{b}",
  "backend": "auto",
  "engine_name": "pix2tex",
  "engine_ready": true,
  "engine_message": "pix2tex 初始化成功。"
}
```

## 3. 实现说明

- API 层不直接实现 OCR 逻辑，统一调用 `services/formula_service.py`
- GUI 与 API 共用同一套识别服务，避免重复实现
- 服务层对模型做了单例复用，减少重复加载开销
