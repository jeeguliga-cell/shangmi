# 尚米 — 高德地图 POI 搜索模块
# 调用高德地图开放平台 API 搜索商家

import requests
import time
from config import GAODE_API_KEY

# 高德搜索 API 地址
GAODE_URL = "https://restapi.amap.com/v3/place/text"


def search_businesses(keyword, city="", page=1, page_size=25):
    """
    搜索商家

    参数:
        keyword: 搜索关键词，如 "川菜馆"
        city:    城市名称，如 "北京"（留空则全国搜索）
        page:    页码（从1开始）
        page_size: 每页数量（最大25）

    返回:
        {
            "success": True/False,
            "total": 总条数,
            "count": 当前页条数,
            "businesses": [...],
            "source": "gaode"
        }
    """
    if not GAODE_API_KEY or GAODE_API_KEY == "你的高德API Key填在这里":
        return {
            "success": False,
            "error": "高德API Key 未配置，请在 config.py 中填入你的 Key",
            "source": "gaode"
        }

    params = {
        "key": GAODE_API_KEY,
        "keywords": keyword,
        "city": city,
        "citylimit": "true",       # 限制在当前城市
        "offset": page_size,       # 每页条数
        "page": page,              # 页码
        "extensions": "all",       # 返回全部信息（评分、人均消费等）
        "output": "JSON"
    }

    try:
        resp = requests.get(GAODE_URL, params=params, timeout=15)
        data = resp.json()
    except Exception as e:
        return {"success": False, "error": f"请求失败: {str(e)}", "source": "gaode"}

    if data.get("status") != "1":
        error_msg = data.get("info", "未知错误")
        return {"success": False, "error": f"高德API返回错误: {error_msg}", "source": "gaode"}

    pois = data.get("pois", [])
    total = int(data.get("count", 0)) or int(data.get("total", 0))

    businesses = []
    for poi in pois:
        # 高德返回的电话可能有多条（分号分隔）
        phone = poi.get("tel", "") or ""

        businesses.append({
            "name": poi.get("name", ""),
            "phone": phone,
            "address": poi.get("address", ""),
            "city": poi.get("cityname", city),
            "district": poi.get("adname", ""),       # 区/县
            "category": poi.get("type", ""),          # 分类（如"餐饮服务 > 中餐厅"）
            "rating": poi.get("biz_ext", {}).get("rating", ""),       # 评分
            "cost": poi.get("biz_ext", {}).get("cost", ""),           # 人均消费
            "location": poi.get("location", ""),      # 经纬度
            "source": "gaode"
        })

    return {
        "success": True,
        "total": total,
        "count": len(businesses),
        "page": page,
        "businesses": businesses,
        "source": "gaode"
    }


def search_all(keyword, city="", max_results=200):
    """
    搜索所有商家（自动翻页）

    参数:
        keyword: 搜索关键词
        city: 城市名称
        max_results: 最多返回条数（高德每页25条，免费额度5000次/月）

    返回:
        {"success": True/False, "businesses": [...], "source": "gaode", "total_found": N}
    """
    all_biz = []
    page = 1
    page_size = 25

    while len(all_biz) < max_results:
        result = search_businesses(keyword, city, page=page, page_size=page_size)

        if not result.get("success"):
            # 第一页就失败 → 返回错误
            if page == 1:
                return result
            # 翻页失败 → 返回已有的数据
            break

        items = result.get("businesses", [])
        if not items:
            break

        all_biz.extend(items)

        # 如果这一页的数量 < page_size，说明到底了
        if len(items) < page_size:
            break

        page += 1
        time.sleep(0.3)  # 礼貌一点，别打太快

    return {
        "success": True,
        "businesses": all_biz,
        "source": "gaode",
        "total_found": len(all_biz)
    }
