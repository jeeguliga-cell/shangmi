# 尚米 — 后端服务 (FastAPI)
# 提供搜索API + 静态页面 + Excel下载

import os
import sys
import json
import time
import random
from collections import defaultdict
from datetime import datetime, timedelta

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from core.engine import search_businesses
from core.excel import export_to_excel
from config import HOST, PORT

app = FastAPI(title="尚米 — 商家数据一键导出")

# 挂载静态文件
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ===== Rate Limiter =====
class RateLimiter:
    """简易IP频率限制，防止爬虫和滥用"""
    def __init__(self, max_per_minute=10):
        self.max_per_minute = max_per_minute
        self.records = defaultdict(list)

    def check(self, ip: str) -> bool:
        now = datetime.now()
        cutoff = now - timedelta(minutes=1)
        # 清理过期记录
        self.records[ip] = [t for t in self.records[ip] if t > cutoff]
        if len(self.records[ip]) >= self.max_per_minute:
            return False
        self.records[ip].append(now)
        return True

limiter = RateLimiter(max_per_minute=10)


# ===== 首页 =====
@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = os.path.join(static_dir, "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>尚米</h1><p>加载中...</p>")


# ===== 搜索API =====
@app.get("/api/search")
async def api_search(
    request: Request,
    keyword: str = Query(..., description="搜索关键词"),
    city: str = Query("", description="城市名称"),
    max_results: int = Query(200, description="最多返回条数"),
):
    # === Rate limit check ===
    client_ip = request.client.host if request.client else "unknown"
    if not limiter.check(client_ip):
        return JSONResponse({
            "success": False,
            "error": "请求太频繁，请稍后再试",
            "businesses": []
        }, status_code=429)

    # === 搜索 ===
    start = time.time()
    result = search_businesses(keyword, city, max_results)
    elapsed = round(time.time() - start, 2)

    if not result.get("success"):
        return JSONResponse({
            "success": False,
            "error": "搜索暂时无结果，请换关键词试试",
            "businesses": [],
            "elapsed": elapsed
        })

    return {
        "success": True,
        "keyword": keyword,
        "city": city,
        "total": result.get("matched", 0),
        "businesses": result.get("businesses", []),
        "elapsed": elapsed
    }


# ===== Excel下载API =====
@app.get("/api/download")
async def api_download(
    keyword: str = Query(..., description="搜索关键词"),
    city: str = Query("", description="城市名称"),
    max_results: int = Query(200, description="最多返回条数"),
):
    """
    搜索并下载 Excel 文件
    """
    result = search_businesses(keyword, city, max_results)

    if not result.get("success"):
        return JSONResponse({
            "success": False,
            "error": result.get("error", "搜索失败")
        })

    businesses = result.get("businesses", [])
    if not businesses:
        return JSONResponse({
            "success": False,
            "error": "没有找到商家数据"
        })

    # 文件名：尚米_城市关键词_条数_时间戳.xlsx
    city_part = city if city else "全国"
    safe_keyword = keyword.replace(" ", "_").replace("/", "_")
    filename = f"尚米_{city_part}{safe_keyword}_{len(businesses)}家.xlsx"
    filepath = os.path.join(os.path.dirname(__file__), "data", filename)

    try:
        export_to_excel(businesses, filepath, keyword)
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": f"导出Excel失败: {str(e)}"
        })

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# ===== 启动 =====
if __name__ == "__main__":
    print(f"""
    ╔══════════════════════════════════════╗
    ║                                      ║
    ║          🏪  商  觅                  ║
    ║     商家数据一键导出工具              ║
    ║                                      ║
    ║  打开浏览器访问：                    ║
    ║  http://localhost:{PORT}              ║
    ║                                      ║
    ║  （如果在同一台电脑上）              ║
    ║  手机上访问（记得连同一个WiFi）：    ║
    ║  http://你的IP地址:{PORT}             ║
    ║                                      ║
    ╚══════════════════════════════════════╝
    """)
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
