from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

app = FastAPI()

# テンプレートフォルダの場所を指定
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # index.html にデータを渡して表示
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "釣果記録＆共有掲示板",
        "message": "Docker + FastAPI + Jinja2 環境構築成功！"
    })