# 尚米 — 百度地图 POI 搜索模块
# 调用百度地图开放平台 API 搜索商家

import requests
import time
from config import BAIDU_API_KEY

# 百度搜索 API 地址
BAIDU_URL = "https://api.map.baidu.com/place/v2/search"


def search_businesses(keyword, city="", page=0, page_size=20):
    """
    搜索商家

    参数:
        keyword: 搜索关键词
        city: 城市名称
        page: 页码（从0开始）
        page_size: 每页数量（最大20）

    返回:
        {"success": True/False, "total": N, "businesses": [...], "source": "baidu"}
    """
    if not BAIDU_API_KEY or BAIDU_API_KEY == "你的百度API Key填在这里":
        return {
            "success": False,
            "error": "百度API Key 未配置，请在 config.py 中填入你的 Key",
            "source": "baidu"
        }

    params = {
        "query": keyword,
        "region": city,
        "city_limit": "true",
        "output": "json",
        "ak": BAIDU_API_KEY,
        "page_size": page_size,
        "page_num": page,
        "scope": "2"  # 返回详细数据（含电话、营业时间等）
    }

    try:
        resp = requests.get(BAIDU_URL, params=params, timeout=15)
        data = resp.json()
    except Exception as e:
        return {"success": False, "error": f"请求失败: {str(e)}", "source": "baidu"}

    if data.get("status") != 0:
        error_msg = data.get("message", "未知错误")
        return {"success": False, "error": f"百度API返回错误: {error_msg}", "source": "baidu"}

    results = data.get("results", [])
    total = data.get("total", 0)

    businesses = []
    for poi in results:
        detail = poi.get("detail_info", {})
        phone = poi.get("telephone", "") or ""

        businesses.append({
            "name": poi.get("name", ""),
            "phone": phone,
            "address": poi.get("address", ""),
            "city": poi.get("city", city),
            "district": poi.get("area", ""),
            "category": poi.get("type", ""),
            "rating": detail.get("overall_rating", ""),
            "shop_hours": detail.get("shop_hours", ""),   # 营业时间（百度独有！）
            "price": detail.get("price", ""),              # 价格/人均（百度独有！）
            "location": f"{poi.get('location', {}).get('lat', '')},{poi.get('location', {}).get('lng', '')}",
            "source": "baidu"
        })

    return {
        "success": True,
        "total": total,
        "count": len(businesses),
        "page": page,
        "businesses": businesses,
        "source": "baidu"
    }


def search_all(keyword, city="", max_results=200):
    """
    搜索所有商家（自动翻页）
    """
    all_biz = []
    page = 0
    page_size = 20

    while len(all_biz) < max_results:
        result = search_businesses(keyword, city, page=page, page_size=page_size)

        if not result.get("success"):
            if page == 0:
                return result
            break

        items = result.get("businesses", [])
        if not items:
            break

        all_biz.extend(items)

        if len(items) < page_size:
            break

        page += 1
        time.sleep(0.3)

    return {
        "success": True,
        "businesses": all_biz,
        "source": "baidu",
        "total_found": len(all_biz)
    }
