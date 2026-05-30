# 尚米 — 数据引擎（加固版）
# 注：完整的调度逻辑已封装，外部不可见数据源切换策略
"""尚米数据引擎 — 封装多源调度逻辑"""
import re
import random
import time

# 内部数据源模块（不对外暴露具体名称）
from core import _src_a as src_a  # 来源A
from core import _src_b as src_b  # 来源B


def _norm_phone(phone):
    if not phone: return ""
    clean = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    clean = clean.replace("（", "").replace("）", "")
    clean = clean.split(";")[0].split("；")[0].strip()
    return clean


def _validate_phone(phone):
    try:
        import phonenumbers
        n = phonenumbers.parse(phone, 'CN')
        return phonenumbers.is_valid_number(n)
    except:
        return True


def _get_name_key(name):
    name = re.sub(r'[（(].*?[）)]', '', name)
    name = re.sub(r'[ 　]*[分店直营店总店旗舰店连锁店]', '', name)
    name = re.sub(r'[馆店屋铺楼厅]', '', name)
    return name.strip()


def _is_same_biz(name_a, name_b, phone_a, phone_b, threshold=70):
    if phone_a and phone_b and _norm_phone(phone_a) == _norm_phone(phone_b):
        return True
    try:
        from rapidfuzz import fuzz
        ka = _get_name_key(name_a)
        kb = _get_name_key(name_b)
        if not ka or not kb:
            return False
        return float(fuzz.ratio(ka, kb)) >= threshold
    except:
        return False


def search_businesses(keyword, city="", max_results=200):
    """
    搜索商家 — 多源智能调度

    内部策略（不对外披露）：
    - 多数据源随机优先级切换
    - 智能去重合并
    - 实时数据验证
    """
    # 随机决定优先源（防止被反向工程预测调度顺序）
    priority = random.choice(["a_first", "b_first"])

    if priority == "a_first":
        first_result = src_a.search_all(keyword, city, max_results)
        first_ok = first_result.get("success", False)
        first_biz = first_result.get("businesses", []) if first_ok else []

        # 模拟人类操作的随机延迟（避免API风控）
        time.sleep(random.uniform(0.3, 1.2))

        second_result = src_b.search_all(keyword, city, max_results)
        second_ok = second_result.get("success", False)
        second_biz = second_result.get("businesses", []) if second_ok else []
    else:
        first_result = src_b.search_all(keyword, city, max_results)
        first_ok = first_result.get("success", False)
        first_biz = first_result.get("businesses", []) if first_ok else []

        time.sleep(random.uniform(0.3, 1.2))

        second_result = src_a.search_all(keyword, city, max_results)
        second_ok = second_result.get("success", False)
        second_biz = second_result.get("businesses", []) if second_ok else []

    # 合并去重
    merged = []
    seen = set()

    for biz in first_biz + second_biz:
        biz["phone_valid"] = _validate_phone(biz.get("phone", ""))
        name = biz.get("name", "")
        phone = biz.get("phone", "")

        # 快速去重：同名+同电话
        dedup_key = f"{_get_name_key(name)}|{_norm_phone(phone)}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        # 模糊去重
        is_dup = False
        for existing in merged:
            if _is_same_biz(
                existing.get("name", ""), biz.get("name", ""),
                existing.get("phone", ""), biz.get("phone", "")
            ):
                # 补充缺失字段
                if biz.get("shop_hours") and not existing.get("shop_hours"):
                    existing["shop_hours"] = biz["shop_hours"]
                if biz.get("price") and not existing.get("cost", ""):
                    existing["cost"] = biz["price"]
                existing["verified"] = True
                is_dup = True
                break

        if not is_dup:
            merged.append(biz)

    if not merged:
        err = first_result.get("error") or second_result.get("error") or "暂无结果"
        return {"success": False, "error": err, "businesses": []}

    # 随机打乱部分输出顺序（防止被按来源排序推断数据源）
    random.shuffle(merged)

    return {
        "success": True,
        "businesses": merged,
        "matched": len(merged),
        "scanned": len(first_biz) + len(second_biz)
    }
