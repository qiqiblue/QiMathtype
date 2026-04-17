# 开发文档（MVP）

## 1. 目标

本项目用于将公式图片识别为 LaTeX，当前版本是最小可用 MVP，专注：

- 本地离线桌面交互
- 单图识别流程闭环
- 可替换 OCR 后端接口

不包含数据库、账号系统、联网服务等复杂能力。

## 2. 模块说明

### `main.py`

- 程序入口
- 创建 `QApplication` 和主窗口

### `ui/main_window.py`

- 主界面布局和交互逻辑
- 支持打开图片、拖拽图片、粘贴剪贴板图片
- 使用 `QThread + Worker` 进行后台识别
- 负责 LaTeX 文本展示和公式预览渲染

### `ocr/formula_engine.py`

- OCR 引擎封装层，对外暴露统一方法：
  - `recognize_formula(image) -> str`
- 后端选择优先级：
  1. `pix2tex`
  2. `pix2text`
- 内置版本兼容判断，减少上层耦合

### `utils/image_preprocess.py`

- 图片加载与预处理（灰度、对比度增强）
- `QImage` 与 `PIL.Image` 的互转

## 3. 后台线程设计

识别任务通过 `OCRWorker` 在 `QThread` 中执行，主线程只负责 UI 更新：

1. 点击“识别”
2. 创建线程与 worker
3. worker 执行预处理 + OCR
4. 通过信号返回识别结果
5. 主线程更新文本与预览并清理线程对象

这样可以避免模型推理阻塞 UI。

## 4. OCR 后端扩展指南

如果你要替换模型（例如接入其他公式 OCR）：

1. 在 `FormulaEngine` 中新增初始化方法（如 `_init_xxx`）
2. 在 `recognize_formula` 中分发到对应识别函数
3. 保持返回值为 `str`（LaTeX）

上层 UI 无需改动。

## 5. 常见问题

### 5.1 识别结果提示“引擎未就绪”

表示 `pix2tex/pix2text` 未正确安装，请先执行：

```bash
pip install -r requirements.txt
```

### 5.2 预览失败

预览使用 `matplotlib.mathtext` 渲染，若 LaTeX 语法不完整会报错。  
可先手动修改右侧 LaTeX 文本，再查看预览。

## 6. 运行与打包建议（后续）

MVP 阶段只要求可运行。后续可选：

- 使用 `PyInstaller` 打包
- 增加批量识别
- 增加识别历史
- 增加截图 OCR
