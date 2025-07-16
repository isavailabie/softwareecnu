import json
from typing import List

from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .models import Recipe, RecipeFlat, EnergyRequirement, ProteinRequirement
from django.utils import timezone
import datetime, re, random


def _score_recipe(recipe: RecipeFlat, provided: set, target_calories: float) -> float:
    """综合打分：
    1. 热量差距得分 (越接近越高)
    2. 食材覆盖率得分 (覆盖≥40% 才合格)
    总分 = 0.6 * 热量得分 + 0.4 * 覆盖率
    """
    # 热量
    cal_str = recipe.calories or "0"
    m = re.search(r"(\d+)", cal_str)
    cal_value = float(m.group(1)) if m else 0.0
    calorie_diff_ratio = abs(cal_value - target_calories) / target_calories if target_calories else 1
    calorie_score = max(0.0, 1 - calorie_diff_ratio)  # 误差 0 -> 1 分

    # 覆盖率
    ing_raw = recipe.ingredients or []
    if isinstance(ing_raw, str):
        try:
            ing_list = json.loads(ing_raw)
        except Exception:
            ing_list = []
    else:
        ing_list = ing_raw
    ing_names = {i.get("name", "").lower() for i in ing_list if i.get("name")}
    if not ing_names:
        cover_score = 0.0
    else:
        cover_ratio = len(ing_names & provided) / len(ing_names)
        cover_score = cover_ratio
    if cover_score == 0:
        return 0.0  # 无任何可用食材则淘汰
    return 0.6 * calorie_score + 0.4 * cover_score


@csrf_exempt  # 先关闭 CSRF，后期可改为 token 鉴权
@require_POST
def recommend_view(request: HttpRequest):
    """POST /recommender/recommend/

    请求 JSON 格式：
    {
        "physical_data": [
            {"user_id": "user1", "height": 175, "weight": 68, "age": 32, "activity_level": "moderate"},
            ...
        ],
        "history": [
            {"date": "2023-07-01", "dishes": ["a", "b", "c"]},
            ...
        ],
        "available_ingredients": ["tomato", "egg", ...]
    }
    其中 available_ingredients 字段也兼容旧字段名 ingredients。
    返回：
    {
        "recipes": [
            {"id": 1, "title": "番茄炒蛋", "score": 1.0},
            ...
        ]
    }
    """

    try:
        body = json.loads(request.body.decode())
        print(f"[Recommend] request_body={body}")
        # 兼容字段名：优先使用新字段 available_ingredients，其次回退到旧字段 ingredients
        ing_list: List[str] = body.get("available_ingredients") or body.get("ingredients", [])
        physical_list = body.get("physical_data", [])
        history_list = body.get("history", [])

        # 基本校验
        if not isinstance(ing_list, list) or not isinstance(physical_list, list) or not isinstance(history_list, list):
            raise ValueError("Invalid payload structure")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"detail": "Invalid JSON"}, status=400)

    provided_set = {i.lower() for i in ing_list}

    # ------------- 实际推荐逻辑 -------------
    # 1. 推断当前餐次
    now = timezone.localtime()
    minutes = now.hour * 60 + now.minute
    if minutes < 9 * 60 + 30:
        meal_percent = 0.275  # 早餐
    elif minutes < 14 * 60 + 30:
        meal_percent = 0.375  # 午餐
    else:
        meal_percent = 0.275  # 晚餐

    # 2. 获取第一个用户体征，简单支持单用户
    if physical_list:
        pdata = physical_list[0]
        age = int(pdata.get("age", 30))
        sex = pdata.get("sex", "M")[:1].upper()  # M / F
        act_map = {"sedentary": "I", "light": "I", "moderate": "II", "active": "III"}
        pal = act_map.get(pdata.get("activity_level", "moderate"), "II")
    else:
        age, sex, pal = 30, "M", "II"

    enr = EnergyRequirement.objects.using("recommend").filter(
        sex=sex, pal_level=pal, age_min__lte=age, age_max__gte=age
    ).first()
    if enr:
        total_calories = float(re.search(r"(\d+)", enr.value).group(1))
    else:
        total_calories = 2000.0  # fallback

    target_calories = total_calories * meal_percent

    # DEBUG 输出能量计算信息
    print(f"[Recommend] age={age}, sex={sex}, pal={pal}, total_cal={total_calories}, meal_percent={meal_percent}, target_cal={target_calories}")

    # 3. 计算食材集合
    provided = {i.lower() for i in ing_list}
    history_titles = {dish.lower() for record in history_list for dish in record.get("dishes", [])}

    # 4. 为所有 RecipeFlat 计算得分
    candidates = []
    for r in RecipeFlat.objects.using("recommend").all():
        if r.title.lower() in history_titles:
            continue
        score = _score_recipe(r, provided, target_calories)
        if score > 0:
            candidates.append((score, r))

    # 5. 排序并取前 9 条
    candidates.sort(key=lambda x: x[0], reverse=True)

    print(f"[Recommend] candidate_with_score={len(candidates)}")
    if candidates:
        top = candidates[:9]
        result = [
            {
                "id": r.id,
                "title": r.title,
                "image_url": r.image_url,
                "calories": r.calories,
                "category": r.category,
                "score": round(score, 3),
                "cook_time": r.cook_time,
                "difficulty": r.difficulty,
                "ingredients": r.ingredients,
            }
            for score, r in top
        ]
        print(f"[Recommend] available_ing={len(provided)}, history_titles={len(history_titles)}")
    else:
        # 无匹配时随机返回 9 道（排除历史记录）
        qs = RecipeFlat.objects.using("recommend").exclude(title__in=list(history_titles))
        sample = random.sample(list(qs[:100]), k=min(9, qs.count())) if qs.exists() else []
        result = [
            {
                "id": r.id,
                "title": r.title,
                "image_url": r.image_url,
                "calories": r.calories,
                "category": r.category,
                "score": 0.0,
                "cook_time": r.cook_time,
                "difficulty": r.difficulty,
                "ingredients": r.ingredients,
            }
            for r in sample
        ]

    return JsonResponse({"recipes": result})
