from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routers.formula import router as formula_router

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"
INDEX_FILE = TEMPLATES_DIR / "index.html"


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例。"""
    app = FastAPI(
        title="QiMathType API",
        version="0.1.0",
        description="公式图片识别为 LaTeX 的 API 服务（MVP）。",
    )

    # MVP 阶段放宽跨域，便于本地 Web 前端联调
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(formula_router)

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    def web_index():
        if INDEX_FILE.exists():
            return FileResponse(str(INDEX_FILE))
        return {
            "service": "QiMathType API",
            "docs": "/docs",
            "health": "/api/v1/health",
        }

    @app.get("/api-info", tags=["meta"])
    def api_info() -> dict[str, str]:
        return {
            "service": "QiMathType API",
            "docs": "/docs",
            "health": "/api/v1/health",
            "recognize": "/api/v1/formula/recognize",
        }

    return app


app = create_app()
