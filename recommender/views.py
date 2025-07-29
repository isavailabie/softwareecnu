import json
from typing import List

from django.http import JsonResponse, HttpRequest
from django.db import IntegrityError
from .models import TempRecipeFlat
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .models import Recipe, RecipeFlat, EnergyRequirement, ProteinRequirement
from django.utils import timezone
import datetime, re, random, os, requests, base64, uuid
from django.conf import settings


def _cal_num(cal_str: str) -> float:
    """Extract number value from a calorie string like '200kcal/100g'."""
    import re
    m = re.search(r"(\d+)", cal_str or "")
    return float(m.group(1)) if m else 0.0


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

    # -------- 组合推荐：一菜一汤 或 一菜一凉菜 ---------

    # 分类列表
    recai_list, tanggeng_list, liangcai_list = [], [], []
    for score, r in candidates:
        cat = (r.category or "").lower()
        if cat == "recai":
            recai_list.append((score, r))
        elif cat == "tanggeng":
            tanggeng_list.append((score, r))
        elif cat == "liangcai":
            liangcai_list.append((score, r))

    # 若某类不足则补随机，但仍保持列表类型存在
    random.shuffle(tanggeng_list)
    random.shuffle(liangcai_list)

    combos: list[tuple[float, RecipeFlat, RecipeFlat, float]] = []  # (combo_score, main, side, total_cal)
    for m_score, m_rec in recai_list[:30]:
        for s_score, s_rec in (tanggeng_list[:30] + liangcai_list[:30]):
            total_cal = _cal_num(m_rec.calories) + _cal_num(s_rec.calories)
            if total_cal <= target_calories:
                combo_score = (m_score + s_score) / 2
                combos.append((combo_score, m_rec, s_rec, total_cal))
        if len(combos) >= 50:
            break

    # 排序并取前 9 组
    combos.sort(key=lambda x: x[0], reverse=True)
    top_combos = combos[:9]

    def _serialize(r: RecipeFlat):
        return {
            "id": r.id,
            "title": r.title,
            "image_url": r.image_url,
            "calories": r.calories,
            "category": r.category,
            "cook_time": r.cook_time,
            "difficulty": r.difficulty,
            "ingredients": r.ingredients,
            "nutrition": getattr(r, "nutrition", None),
            "description": getattr(r, "description", ""),
        }

    local_combos = [
        {
            "main": _serialize(main),
            "side": _serialize(side),
            "total_calories": round(tcal, 1),
            "score": round(cs, 3),
        }
        for cs, main, side, tcal in top_combos
    ]

    # ---------------- AI 组合补充 ----------------
    def _generate_image(title: str) -> str:
        """调用 ChatECNU image API 生成菜谱封面，返回图片 URL，失败时返回空字符串。

        优先返回接口中的 ``url`` 字段；若仅返回 ``b64_json``，
        则保存到 ``MEDIA_ROOT/recipes`` 并返回对应 ``MEDIA_URL``。
        """
        api_key = os.getenv("CHATECNU_API_KEY")
        if not api_key:
            return ""

        payload = {
            "prompt": title,
            "model": "ecnu-image",
            "size": "512x512",
        }
        try:
            resp = requests.post(
                "https://chat.ecnu.edu.cn/open/api/v1/images/generations",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                json=payload,
                timeout=60,
            )
            if resp.status_code != 200:
                print(f"[Recommend] image API http={resp.status_code}: {resp.text[:400]}")
                return ""

            data = resp.json().get("data", [])
            if not data:
                print(f"[Recommend] image API empty data for {title}: {resp.text[:400]}")
                return ""

            img_info = data[0]

            # 1. 直接返回 URL
            if img_info.get("url"):
                url = img_info["url"]
                print(f"[Recommend] generated image url for {title}: {url}")
                return url

            # 2. 处理 base64 数据
            b64_data = img_info.get("b64_json")
            if b64_data:
                try:
                    filename = f"{uuid.uuid4().hex}.png"
                    save_dir = os.path.join(settings.MEDIA_ROOT, "recipes")
                    os.makedirs(save_dir, exist_ok=True)
                    file_path = os.path.join(save_dir, filename)
                    with open(file_path, "wb") as f:
                        f.write(base64.b64decode(b64_data))

                    url = settings.MEDIA_URL.rstrip("/") + "/recipes/" + filename
                    print(f"[Recommend] generated local image for {title}: {url}")
                    return url
                except Exception as e:
                    print(f"[Recommend] save b64 image error: {e}")
                    return ""
        except Exception as e:
            print(f"[Recommend] generate image error: {e}")
        return ""

    def _get_ai_combos(ings: list[str], tgt_cal: float):
        api_key = os.getenv("CHATECNU_API_KEY")
        print(f"[Recommend] env CHATECNU_API_KEY present={bool(api_key)}")
        if not api_key:
            return []

        prompt = (
            f"请根据食材列表 {', '.join(ings)} ，推荐 2 组中式组合：每组包含一份热菜(类别 recai)和一份汤羹或凉菜(类别 tanggeng/liangcai)，"
            f"一组严格用食材列表中的食材，另一组用食材列表中的食材和一些其他食材，"
            f"总热量不超过 {round(tgt_cal)} 千卡。"
            "请以 JSON 格式返回，如：{\n"
            "  \"combos\": [\n"
            "    {\n"
            "      \"main\": {\n"
            "        \"title\": \"番茄炒蛋\",\n"
            "        \"category\": \"recai\",\n"
            "        \"calories\": \"300kcal\",\n"
            "        \"ingredients\": [\n"
            "          {\"name\": \"番茄\", \"quantity\": \"100g\"},\n"
            "          {\"name\": \"鸡蛋\", \"quantity\": \"2个\"}\n"
            "        ],\n"
            "        \"steps\": [\"step1\", \"step2\"],\n"
            "        \"nutrition\": {\"脂肪\": \"12g\", \"纤维素\": \"0.5g\", \"碳水\": \"2g\", \"蛋白质\": \"15g\"},\n"
            "        \"cook_time\": \"15分钟\",\n"
            "        \"difficulty\": \"简单\",\n"
            "        \"description\": \"一道经典快手家常菜，酸甜可口，营养丰富。\"\n"
            "      },\n"
            "      \"side\": { ... },\n"
            "      \"total_calories\": 600\n"
            "    }\n"
            "  ]\n"
            "}\n"
            "steps尽可能详细，不要附加解释文字，同时返回 nutrition 字段（键使用中文名称，数值带单位的字符串）、cook_time 字段（示例\"15分钟\"或\"1小时\"）、difficulty 字段（简单/中等/困难三选一）以及一句话 description。"
        )
        payload = {
            "messages": [
                {"role": "system", "content": "你是华东师范大学大模型ChatECNU"},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "model": "ecnu-plus",
        }
        try:
            resp = requests.post(
                "https://chat.ecnu.edu.cn/open/api/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                json=payload,
                timeout=60,
            )
            if resp.status_code == 200:
                print(f"[Recommend] AI status=200, raw={resp.text[:400]}")
                print(f"[Recommend] AI raw response: {resp.text[:400]}")
                choices = resp.json().get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    print(f"[Recommend] AI content={content[:200]}")
                    content_clean = re.sub(r"```(?:json)?|```", "", content).strip()
                    content_clean = re.sub(r"```(?:json)?|```", "", content).strip()
                    try:
                        data = json.loads(content_clean)
                    except json.JSONDecodeError as e:
                        print(f"[Recommend] AI JSON parse error: {e}. raw={content_clean[:200]}")
                        return []
                    return data.get("combos", [])
        except Exception as e:
            print(f"[Recommend] AI recommend error: {e}")
        return []

    ai_combos_raw = _get_ai_combos(list(provided_set), target_calories)[:2]
    # 标准化字段 & 标记 AI 生成
    # 保存 AI 组合到临时表，若已存在则复用
    ai_combos = []
    for c in ai_combos_raw:
        for part in ("main", "side"):
            item = c.get(part, {})
            # name -> title 兼容
            if "title" not in item and "name" in item:
                item["title"] = item.pop("name")
            # ingredients: list[str] -> list[dict]
            ings = item.get("ingredients")
            if isinstance(ings, list) and (not ings or isinstance(ings[0], str)):
                item["ingredients"] = [{"name": n, "quantity": ""} for n in ings]
            # 保存到临时表
            temp_recipe, created = TempRecipeFlat.objects.get_or_create(
                title=item["title"],
                defaults={
                    "image_url": item.get("image_url", ""),
                    "calories": item.get("calories", ""),
                    "category": item.get("category", ""),
                    "cook_time": item.get("cook_time", ""),
                    "difficulty": item.get("difficulty", ""),
                    "ingredients": item.get("ingredients", []),
                    # 新增字段保存
                    "steps": item.get("steps", []),
                    "nutrition": item.get("nutrition"),
                    "description": item.get("description", ""),
                    "servings": item.get("servings", ""),
                },
            )
            # 若已存在但之前未保存步骤等字段，则补充更新
            if not created:
                updated = False
                for field in [
                    ("steps", item.get("steps")),
                    ("nutrition", item.get("nutrition")),
                    ("description", item.get("description")),
                    ("servings", item.get("servings")),
                    ("cook_time", item.get("cook_time")),
                    ("difficulty", item.get("difficulty")),
                ]:
                    fname, fval = field
                    if fval and not getattr(temp_recipe, fname):
                        setattr(temp_recipe, fname, fval)
                        updated = True
                if updated:
                    try:
                        temp_recipe.save()
                    except IntegrityError:
                        pass
            # 若缺少图片，自动调用图片生成
            if not temp_recipe.image_url:
                img_url = _generate_image(temp_recipe.title)
                if img_url:
                    temp_recipe.image_url = img_url
                    try:
                        temp_recipe.save(update_fields=["image_url"])
                    except IntegrityError:
                        pass
            if created:
                print(f"[Recommend] [TempRecipe] saved: {temp_recipe.title}")
            item_dict = _serialize(temp_recipe)
            item_dict["title"] = item_dict.get("title", "") + "（AI生成）"
            # 保留 AI 返回的详细用量和步骤信息
            if "steps" in item:
                item_dict["steps"] = item["steps"]
            if "ingredients" in item:
                item_dict["ingredients"] = item["ingredients"]
            if "nutrition" in item:
                item_dict["nutrition"] = item["nutrition"]
            if "description" in item:
                item_dict["description"] = item["description"]
            if "cook_time" in item:
                item_dict["cook_time"] = item["cook_time"]
            if "difficulty" in item:
                item_dict["difficulty"] = item["difficulty"]
            # 确保返回最新图片链接
            item_dict["image_url"] = temp_recipe.image_url
            c[part] = item_dict

    

    # ---- 构造最终列表：最多 7 本地 + 若干 AI(<=2) ----
    final_combos = local_combos[:7]  # 先取前 7 条数据库结果
    insert_positions = [2, 5]  # 目标插入索引
    for idx, ai_combo in enumerate(ai_combos_raw):
        pos = insert_positions[idx]
        if pos <= len(final_combos):
            final_combos.insert(pos, ai_combo)
        else:
            final_combos.append(ai_combo)

    return JsonResponse({"combos": final_combos})
