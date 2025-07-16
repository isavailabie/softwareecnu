import json
from typing import List

from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .models import Recipe


def _score_recipe(recipe: Recipe, provided: set) -> float:
    """简单打分：完全包含给 1.0，缺失给 0.5。"""
    ingredients = set(recipe.ingredients.values_list("name", flat=True))
    missing = ingredients - provided
    return 1.0 if not missing else 0.5


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

    # 暂时不访问数据库，固定返回示例菜谱列表。
    sample_recipe = {
        "id": 1,
        "dish_name": "刀豆焖排骨",
        "title": "刀豆焖排骨",  # 为兼容旧字段
        "image_url": "https://i3.meishichina.com/atta/recipe/2025/07/07/202507071751856530463474389860.jpg?x-oss-process=style/p800",
        "image_path": "images/刀豆焖排骨.jpg",
        "ingredients": [
            {"name": "排骨", "amount": "400g"},
            {"name": "蒜头", "amount": "2瓣"},
            {"name": "盐", "amount": "半匙"},
            {"name": "辣椒粉", "amount": "少许"},
            {"name": "蚝油", "amount": "1勺"}
        ],
        "steps": [
            "刀豆洗净切段备用。",
            "排骨洗净用少许生粉、生抽腌制20分钟。",
            "蒜头切片。",
            "锅中倒入适量油，下蒜头爆香。",
            "下排骨翻炒一下。",
            "再下入刀豆，翻炒一下。",
            "撒入盐。",
            "加蚝油。",
            "撒入辣椒粉，翻炒均匀。",
            "倒入一碗清水，中小火焖煮20分钟左右即可。"
        ],
        "calories": "1170大卡",
        "nutrition": {
            "energy": "1170千卡",
            "protein": "55克",
            "fat": "80克",
            "carbohydrates": "10克",
            "fiber": "3克",
            "sodium": "2500毫克"
        },
        "description": "这道菜将鲜嫩的排骨与清香的刀豆结合，口感丰富，咸香适口，是一道家常下饭菜。",
        "cook_time": "40分钟",
        "difficulty": "中等",
        "servings": "4人份",
        "score": 1.0
    }

    return JsonResponse({"recipes": [sample_recipe]})
