from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import CartItem, Recipe, Ingredient, RecipeIngredient, FavoriteIngredient, FridgeItem, UserCalorieRecord, UserProfile
from django.utils import timezone
from recommender.models import RecipeFlat
import datetime
import json

import os
import base64
import io
import requests
from django.conf import settings
from PIL import Image

# 常用佐料/调味品列表：忽略匹配和显示
CONDIMENTS = {
    '葱花', '姜末', '蒜末', '料酒', '酱油', '白砂糖', '醋', '水淀粉', '干淀粉', '食用油','香醋','白糖','鸡精','姜','盐','清水'
}

# 商品数据（实际项目应从数据库获取）
PRODUCTS = [
    {'id': 1, 'name': '有机苹果 650g', 'price': 11.80, 'image_url': '/static/fruit/images/apple.jpg', 'category': '水果', 'description': '新鲜采摘，自然成熟，无农药残留', 'tag': '热卖'},
    {'id': 2, 'name': '有机西兰花 500g', 'price': 4.99, 'image_url': '/static/fruit/images/broccoli.jpg', 'category': '蔬菜', 'description': '当日采摘，冷链配送，保留最佳营养', 'tag': '新品'},
    {'id': 3, 'name': '精选鸡胸肉 450g', 'price': 9.99, 'image_url': '/static/fruit/images/chicken.jpg', 'category': '肉类', 'description': '无激素添加，低脂高蛋白，健身首选', 'tag': ''},
    {'id': 4, 'name': '鲜活黑虎虾 500g', 'price': 59.90, 'image_url': '/static/fruit/images/shrimp.jpg', 'category': '海鲜', 'description': '深海捕捞，急速冷冻，保持鲜甜口感', 'tag': '特惠'},
    {'id': 5, 'name': '土鸡蛋 30枚', 'price': 19.80, 'image_url': '/static/fruit/images/eggs.jpg', 'category': '蛋类', 'description': '散养土鸡蛋，蛋黄饱满，营养丰富', 'tag': ''},
    {'id': 6, 'name': '有机纯牛奶 1L', 'price': 15.90, 'image_url': '/static/fruit/images/milk.jpg', 'category': '奶制品', 'description': '无添加，高钙高蛋白，家庭装', 'tag': ''},
    {'id': 7, 'name': '有机燕麦片 900g', 'price': 18.80, 'image_url': '/static/fruit/images/oatmeal.jpg', 'category': '谷物', 'description': '全谷物，高纤维，健康早餐首选', 'tag': '限时'},
    {'id': 8, 'name': '特级初榨橄榄油 750ml', 'price': 92.20, 'image_url': '/static/fruit/images/olive-oil.jpg', 'category': '调味品', 'description': '冷压初榨，地中海原装进口', 'tag': ''},
]

# 登录页面
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # 检查用户是否存在
        if not User.objects.filter(username=username).exists():
            messages.error(request, '该用户名不存在，请检查或注册新账号')
            return render(request, 'fruit/login.html')
        
        # 验证密码
        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, '密码错误，请重新输入')
            return render(request, 'fruit/login.html')
        
        # 登录成功
        login(request, user)
        messages.success(request, f'欢迎回来，{username}！')
        return redirect('product_list')
    
    return render(request, 'fruit/login.html')

# 注册页面
def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # 检查用户名是否已存在
        if User.objects.filter(username=username).exists():
            messages.error(request, '该用户名已被注册，请选择其他用户名')
            return redirect('login_view')
        
        # 创建新用户
        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        messages.success(request, f'账号创建成功，欢迎 {username}！')
        return redirect('product_list')
    
    return redirect('login_view')

# 退出登录
def logout_view(request):
    logout(request)
    messages.success(request, '您已成功退出登录')
    return redirect('login_view')

# 商品列表页视图
def product_list(request):
    # 如果用户未登录，重定向到登录页面
    if not request.user.is_authenticated:
        return redirect('login_view')
    
    return render(request, 'fruit/index.html', {'products': PRODUCTS})

# 加入购物车视图
def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': '请先登录'})
    
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        product = next((p for p in PRODUCTS if p['id'] == product_id), None)
        
        if not product:
            return JsonResponse({'success': False})
            
        quantity = int(request.POST.get('quantity', 1))
        
        # 尝试获取已存在的购物车项目
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            product_id=product_id,
            defaults={
                'name': product['name'],
                'price': product['price'],
                'image_url': product['image_url'],
                'category': product['category'],
                'description': product['description'],
                'tag': product['tag'],
                'quantity': quantity
            }
        )
        
        # 如果购物车项目已存在，增加数量
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False}, status=405)

# 购物车页面
def cart_view(request):
    if not request.user.is_authenticated:
        return redirect('login_view')
    
    # 从数据库获取购物车项目
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.price * item.quantity for item in cart_items)
    # 将总金额保留两位小数
    total = round(total, 2)
    
    return render(request, 'fruit/cart.html', {'cart_items': cart_items, 'total': total})

# 更新购物车
def update_cart(request, product_id):
    if not request.user.is_authenticated:
        return redirect('login_view')
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        try:
            cart_item = CartItem.objects.get(user=request.user, product_id=product_id)
            
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
            else:
                cart_item.delete()
        except CartItem.DoesNotExist:
            pass
    
    return redirect('cart_view')

# 从购物车中删除
def remove_from_cart(request, product_id):
    if not request.user.is_authenticated:
        return redirect('login_view')
    
    try:
        cart_item = CartItem.objects.get(user=request.user, product_id=product_id)
        cart_item.delete()
    except CartItem.DoesNotExist:
        pass
    
    return redirect('cart_view')

# 我的页面
@login_required
def toggle_favorite_ingredient(request):
    """收藏 / 取消收藏食材 (AJAX POST)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '请求方法错误'})

    name = request.POST.get('name', '').strip()
    if not name:
        return JsonResponse({'success': False, 'error': '名称不能为空'})

    fav, created = FavoriteIngredient.objects.get_or_create(user=request.user, name=name)
    if not created:
        fav.delete()
        return JsonResponse({'success': True, 'is_favorited': False})
    return JsonResponse({'success': True, 'is_favorited': True})


@login_required
def check_favorite_status(request):
    """前端加载时检查收藏状态"""
    name = request.GET.get('name', '').strip()
    if not name:
        return JsonResponse({'success': False, 'error': '名称不能为空'})
    is_favorited = FavoriteIngredient.objects.filter(user=request.user, name=name).exists()
    return JsonResponse({'success': True, 'is_favorited': is_favorited})


@login_required
def add_to_fridge(request):
    """向冰箱添加食材 (AJAX POST)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '请求方法错误'})

    name = request.POST.get('name', '').strip()
    quantity = int(request.POST.get('quantity', 1))
    source = request.POST.get('source', 'recognized')

    if not name:
        return JsonResponse({'success': False, 'error': '名称不能为空'})

    item, created = FridgeItem.objects.get_or_create(
        user=request.user,
        name=name,
        source=source,
        defaults={'quantity': quantity}
    )
    if not created:
        item.quantity += quantity
        item.save()
    return JsonResponse({'success': True})


@login_required
def fridge_view(request):
    """冰箱页面，显示所有食材"""
    items = FridgeItem.objects.filter(user=request.user)
    return render(request, 'fruit/fridge.html', {'items': items})

# 我的页面
@login_required
def my_view(request):
    # 获取当前日期
    today = timezone.now().date()
    
    # 获取或创建用户个人资料
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # 如果是POST请求，处理表单提交
    if request.method == 'POST':
        # 检查是否是个人信息表单
        if 'update_profile' in request.POST:
            # 更新个人信息
            try:
                height = int(request.POST.get('height', 0)) or None
                weight = float(request.POST.get('weight', 0)) or None
                gender = request.POST.get('gender', '')
                activity_level = request.POST.get('activity_level', 'II')
                birth_date_str = request.POST.get('birth_date', '')
                
                profile.height = height
                profile.weight = weight
                profile.gender = gender if gender else None
                profile.activity_level = activity_level
                
                # 处理生日
                if birth_date_str:
                    try:
                        birth_date = datetime.datetime.strptime(birth_date_str, '%Y-%m-%d').date()
                        profile.birth_date = birth_date
                    except ValueError:
                        messages.error(request, '生日格式无效，请使用YYYY-MM-DD格式')
                
                profile.save()
                
                # 更新用户的热量目标
                recommended_calories = profile.get_recommended_calories()
                
                # 更新今日记录的热量目标（如果存在）
                try:
                    today_record = UserCalorieRecord.objects.get(user=request.user, date=today)
                    today_record.daily_target = recommended_calories
                    today_record.save()
                except UserCalorieRecord.DoesNotExist:
                    pass
                
                messages.success(request, '个人信息已更新！')
                return redirect('my_view')
            except (ValueError, TypeError) as e:
                messages.error(request, f'更新个人信息失败: {str(e)}')
                return redirect('my_view')
        
        # 检查是AJAX请求还是表单提交
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # 处理AJAX请求
            data = json.loads(request.body)
            
            breakfast_food = data.get('breakfast_food', '')
            breakfast_calories = int(data.get('breakfast_calories', 0))
            lunch_food = data.get('lunch_food', '')
            lunch_calories = int(data.get('lunch_calories', 0))
            dinner_food = data.get('dinner_food', '')
            dinner_calories = int(data.get('dinner_calories', 0))
            
            # 获取推荐热量
            recommended_calories = profile.get_recommended_calories()
            
            # 获取或创建今日记录
            record, created = UserCalorieRecord.objects.get_or_create(
                user=request.user,
                date=today,
                defaults={
                    'breakfast_food': breakfast_food,
                    'breakfast_calories': breakfast_calories,
                    'lunch_food': lunch_food,
                    'lunch_calories': lunch_calories,
                    'dinner_food': dinner_food,
                    'dinner_calories': dinner_calories,
                    'daily_target': recommended_calories
                }
            )
            
            # 如果记录已存在，则更新
            if not created:
                record.breakfast_food = breakfast_food
                record.breakfast_calories = breakfast_calories
                record.lunch_food = lunch_food
                record.lunch_calories = lunch_calories
                record.dinner_food = dinner_food
                record.dinner_calories = dinner_calories
                record.save()
            
            # 返回成功响应
            return JsonResponse({
                'success': True,
                'total': record.total_calories,
                'remaining': record.remaining_calories,
                'percentage': record.completion_percentage,
                'status': record.status
            })
        else:
            # 处理常规表单提交
            breakfast_food = request.POST.get('breakfast_food', '')
            breakfast_calories = int(request.POST.get('breakfast_calories', 0))
            lunch_food = request.POST.get('lunch_food', '')
            lunch_calories = int(request.POST.get('lunch_calories', 0))
            dinner_food = request.POST.get('dinner_food', '')
            dinner_calories = int(request.POST.get('dinner_calories', 0))
            
            # 获取推荐热量
            recommended_calories = profile.get_recommended_calories()
            
            # 获取或创建今日记录
            record, created = UserCalorieRecord.objects.get_or_create(
                user=request.user,
                date=today,
                defaults={
                    'breakfast_food': breakfast_food,
                    'breakfast_calories': breakfast_calories,
                    'lunch_food': lunch_food,
                    'lunch_calories': lunch_calories,
                    'dinner_food': dinner_food,
                    'dinner_calories': dinner_calories,
                    'daily_target': recommended_calories
                }
            )
            
            # 如果记录已存在，则更新
            if not created:
                record.breakfast_food = breakfast_food
                record.breakfast_calories = breakfast_calories
                record.lunch_food = lunch_food
                record.lunch_calories = lunch_calories
                record.dinner_food = dinner_food
                record.dinner_calories = dinner_calories
                record.save()
            
            messages.success(request, '热量记录已保存！')
            return redirect('my_view')
    
    # 获取今日记录（如果存在）
    try:
        today_record = UserCalorieRecord.objects.get(user=request.user, date=today)
    except UserCalorieRecord.DoesNotExist:
        today_record = None
    
    # 获取历史记录（最近7天）
    end_date = today
    start_date = end_date - datetime.timedelta(days=6)
    history_records = UserCalorieRecord.objects.filter(
        user=request.user,
        date__range=[start_date, end_date]
    ).order_by('-date')
    
    # 准备图表数据
    chart_data = {
        'week': {
            'labels': [],
            'data': []
        },
        'last-week': {
            'labels': [],
            'data': []
        },
        'month': {
            'labels': [],
            'data': []
        }
    }
    
    # 本周数据
    current_date = today
    for i in range(6, -1, -1):
        date = current_date - datetime.timedelta(days=i)
        weekday = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][date.weekday()]
        chart_data['week']['labels'].append(weekday)
        
        try:
            record = UserCalorieRecord.objects.get(user=request.user, date=date)
            chart_data['week']['data'].append(record.total_calories)
        except UserCalorieRecord.DoesNotExist:
            chart_data['week']['data'].append(0)
    
    # 上周数据
    for i in range(13, 6, -1):
        date = current_date - datetime.timedelta(days=i)
        weekday = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][date.weekday()]
        chart_data['last-week']['labels'].append(weekday)
        
        try:
            record = UserCalorieRecord.objects.get(user=request.user, date=date)
            chart_data['last-week']['data'].append(record.total_calories)
        except UserCalorieRecord.DoesNotExist:
            chart_data['last-week']['data'].append(0)
    
    # 本月数据（按周）
    # 简化处理，每7天为一周
    for i in range(4):
        start = current_date - datetime.timedelta(days=(i+1)*7-1)
        end = current_date - datetime.timedelta(days=i*7)
        chart_data['month']['labels'].append(f'第{4-i}周')
        
        week_records = UserCalorieRecord.objects.filter(
            user=request.user,
            date__range=[start, end]
        )
        if week_records.exists():
            total = sum(record.total_calories for record in week_records)
            chart_data['month']['data'].append(total)
        else:
            chart_data['month']['data'].append(0)
    
    chart_data['month']['labels'].reverse()
    chart_data['month']['data'].reverse()
    
    # 获取推荐热量
    recommended_calories = profile.get_recommended_calories()
    
    context = {
        'today_record': today_record,
        'history_records': history_records,
        'chart_data': json.dumps(chart_data),
        'today_date': today.strftime('%Y年%m月%d日'),
        'profile': profile,
        'recommended_calories': recommended_calories
    }
    
    return render(request, 'fruit/my.html', context)

# 编辑历史热量记录
@login_required
def edit_calorie_record(request, record_id):
    record = get_object_or_404(UserCalorieRecord, id=record_id, user=request.user)
    
    if request.method == 'POST':
        record.breakfast_food = request.POST.get('breakfast_food', '')
        record.breakfast_calories = int(request.POST.get('breakfast_calories', 0))
        record.lunch_food = request.POST.get('lunch_food', '')
        record.lunch_calories = int(request.POST.get('lunch_calories', 0))
        record.dinner_food = request.POST.get('dinner_food', '')
        record.dinner_calories = int(request.POST.get('dinner_calories', 0))
        record.save()
        
        messages.success(request, '记录已更新！')
        return redirect('my_view')
    
    context = {
        'record': record
    }
    
    return render(request, 'fruit/edit_calorie.html', context)

# 菜谱页面
@login_required
def recipe_view(request):
    # 获取推荐菜谱和热门菜谱
    popular_recipes = Recipe.objects.filter(is_popular=True)[:3]
    healthy_recipes = Recipe.objects.filter(is_healthy=True)[:3]
    
    context = {
        'popular_recipes': popular_recipes,
        'healthy_recipes': healthy_recipes
    }
    
    return render(request, 'fruit/recipe.html', context)

# 菜谱推荐API
@login_required
def recommend_recipes(request):
    if request.method == 'POST':
        # 获取用户输入的食材
        ingredients = []
        for i in range(1, 6):
            ingredient_name = request.POST.get(f'ingredient{i}', '').strip()
            if ingredient_name:
                ingredients.append(ingredient_name)
        
        if not ingredients:
            return JsonResponse({'success': False, 'message': '请至少输入一种食材'})
        
        # 1. 先通过关系查询出至少包含其中一个食材的菜谱（去重）
        candidate_recipes = Recipe.objects.filter(ingredients__name__in=ingredients).distinct()

        matching_recipes = []

        for recipe in candidate_recipes:
            # 当前菜谱的全部食材记录
            recipe_ingredients_qs = RecipeIngredient.objects.filter(recipe=recipe).select_related('ingredient')
            recipe_ingredient_names = [ri.ingredient.name for ri in recipe_ingredients_qs if ri.ingredient.name not in CONDIMENTS]

            # 匹配度 = 输入食材与菜谱食材交集 / 菜谱总食材
            matched_ingredients = set(ingredients) & set(recipe_ingredient_names)
            if not matched_ingredients:
                continue  # 理论不会发生，但保险

            match_percentage = len(matched_ingredients) / len(recipe_ingredient_names) * 100
            needs_extra = len(matched_ingredients) < len(recipe_ingredient_names)

            recipe_data = {
                'id': recipe.id,
                'title': recipe.title,
                'cooking_time': recipe.cooking_time,
                'difficulty': recipe.difficulty,
                'image_url': recipe.image_url,
                'match_percentage': int(match_percentage),
                'needs_extra': needs_extra,
                'ingredients': []
            }

            for ri in recipe_ingredients_qs:
                if ri.ingredient.name in CONDIMENTS:
                    continue
                recipe_data['ingredients'].append({
                    'name': ri.ingredient.name,
                    'amount': ri.amount,
                    'is_match': (ri.ingredient.name in CONDIMENTS) or (ri.ingredient.name in matched_ingredients)
                })

            matching_recipes.append(recipe_data)

        # 按匹配度和烹饪时间排序（示例）
        matching_recipes.sort(key=lambda x: (-x['match_percentage'], x['cooking_time']))

        return JsonResponse({'success': True, 'recipes': matching_recipes})
    
    return JsonResponse({'success': False, 'message': '请求方法不正确'})

# 菜谱详情页
@login_required
def recipe_detail(request, recipe_id):
    """菜谱详情：改为从 recommender_recipeflat (RecipeFlat) 读取"""
    recipe = get_object_or_404(RecipeFlat, id=recipe_id)

    # ingredients: list[{name, amount}]
    ingredients_list = [
        {
            'ingredient': {'name': item.get('name', '')},
            'amount': item.get('amount', '')
        }
        for item in (recipe.ingredients or [])
    ]

    # steps: 支持 list / 换行字符串 两种格式
    steps = []
    if isinstance(recipe.steps, list):
        for i, s in enumerate(recipe.steps):
            if not s:
                continue
            if isinstance(s, dict):
                desc = s.get('description') or s.get('step') or ''
                tip = s.get('tip', '')
            else:
                desc = str(s)
                tip = ''
            steps.append({
                'number': i + 1,
                'title': f"步骤 {i + 1}",
                'description': desc.strip(),
                'tip': tip
            })
    elif recipe.steps:
        for i, step_text in enumerate(str(recipe.steps).split('\n')):
            if step_text.strip():
                steps.append({
                    'number': i + 1,
                    'title': f"步骤 {i + 1}",
                    'description': step_text.strip(),
                    'tip': ''
                })

    # 营养信息
    nutrition_data = recipe.nutrition or {}
    if isinstance(nutrition_data, dict):
        nutrition = [{'label': k, 'value': v} for k, v in nutrition_data.items()]
    elif isinstance(nutrition_data, list):
        nutrition = nutrition_data
    else:
        nutrition = []
    
    context = {
        'recipe': recipe,
        'ingredients': ingredients_list,
        'steps': steps,
        'nutrition': nutrition,
        'tips': [],
        'match_percentage': request.GET.get('match', '100%')
    }
    
    return render(request, 'fruit/recipe_detail.html', context)


from django.views.decorators.http import require_POST
from django.test.client import RequestFactory
import json
from recommender.views import recommend_view

@login_required
@require_POST
def healthy_recommend(request):
    """返回为当前用户推荐的健康菜谱，数据来自 recommender.recommend_view"""
    user = request.user
    # 1. 从冰箱收集可用食材
    ing_qs = FridgeItem.objects.filter(user=user).values_list('name', flat=True)
    available_ingredients = list(ing_qs)

    # TODO: 根据实际模型获取用户体征和历史饮食
    physical_data = []
    history = []

    payload = {
        "available_ingredients": available_ingredients,
        "physical_data": physical_data,
        "history": history,
    }

    rf = RequestFactory()
    proxy_req = rf.post('/recommender/recommend/', data=json.dumps(payload), content_type='application/json')
    # 调用 recommender 应用的视图函数
    response = recommend_view(proxy_req)
    data = json.loads(response.content)
    match_set = {name.lower() for name in available_ingredients}

    # 兼容新版 combos 结构
    if "combos" in data:
        for combo in data["combos"]:
            for part in (combo.get("main"), combo.get("side")):
                if not part:
                    continue
                needs_extra = False
                original_ings = part.get("ingredients", []) or []
                # 过滤掉佐料
                filtered_ings = [ing for ing in original_ings if ing.get("name", "").lower() not in CONDIMENTS]
                part["ingredients"] = filtered_ings
                for ing in filtered_ings:
                    n = ing.get("name", "").lower()
                    if n in CONDIMENTS:
                        ing["is_match"] = True
                        continue
                    ing["is_match"] = n in match_set
                    if not ing["is_match"]:
                        needs_extra = True
                part["needs_extra"] = needs_extra
    else:
        # 旧版 recipes 列表
        for rec in data.get("recipes", []):
            needs_extra = False
            original_ings = rec.get("ingredients", []) or []
            filtered_ings = [ing for ing in original_ings if ing.get("name", "").lower() not in CONDIMENTS]
            rec["ingredients"] = filtered_ings
            needs_extra = False
            for ing in filtered_ings:
                n = ing.get("name", "").lower()
                ing["is_match"] = n in match_set
                if not ing["is_match"]:
                    needs_extra = True
            rec["needs_extra"] = needs_extra
        for ing in rec.get("ingredients", []) or []:
            n = ing.get("name", "").lower()
            ing["is_match"] = n in match_set
            if not ing["is_match"]:
                needs_extra = True
        rec["needs_extra"] = needs_extra
    return JsonResponse(data)


def recognize_fruit(request):
    """Fruit and vegetable recognition page"""
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            # 创建输出目录
            output_dir = os.path.join(settings.MEDIA_ROOT, 'recognition')
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 保存上传的图片
            uploaded_file = request.FILES['image']
            image_path = os.path.join(output_dir, uploaded_file.name)
            with open(image_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            # 处理图片并获取识别结果
            results = process_image(image_path)
            
            # 获取图片URL用于显示
            image_url = os.path.join(settings.MEDIA_URL, 'recognition', uploaded_file.name)
            
            return render(request, 'fruit/recognition_result.html', {
                'image_url': image_url,
                'results': results,
                'success': True
            })
            
        except Exception as e:
            return render(request, 'fruit/recognition_result.html', {
                'error': str(e),
                'success': False
            })
    
    return render(request, 'fruit/recognize_fruit.html')

def process_image(image_path):
    """Process the image and return recognition results"""
    MULTI_OBJECT_API = "https://aip.baidubce.com/rest/2.0/image-classify/v1/multi_object_detect"
    INGREDIENT_API = "https://aip.baidubce.com/rest/2.0/image-classify/v1/classify/ingredient"
    ACCESS_TOKEN = "24.80c4f636eb0fe0a74777316cf62ecf31.2592000.1754933089.282335-119491175"
    
    results = []
    
    try:
        # 1. 多主体检测
        detection_result = detect_objects(image_path, MULTI_OBJECT_API, ACCESS_TOKEN)
        if not detection_result or "result" not in detection_result:
            return [{"error": "未检测到任何主体"}]
        
        # 2. 读取原始图像
        original_image = Image.open(image_path)
        
        # 3. 处理每个检测到的主体
        # 仅处理果蔬主体，忽略其它（如餐具、包装等）
        fruit_objects = [o for o in detection_result.get("result", []) if o.get("name") == "果蔬生鲜"]
        for i, obj in enumerate(fruit_objects):
            # 获取位置信息
            loc = obj["location"]
            left, top, width, height = loc["left"], loc["top"], loc["width"], loc["height"]
            
            # 裁剪对象区域
            cropped = original_image.crop((left, top, left + width, top + height))
            
            # 进行细粒度识别
            name, score = recognize_ingredient(cropped, i, INGREDIENT_API, ACCESS_TOKEN)
            
            # 如果细粒度识别没有结果，使用检测到的类别
            if not name and "name" in obj:
                name = obj["name"]
                score = obj.get("score", 0)  # 使用检测的置信度
            
            if name:
                # 简化结果，只保留名称和置信度
                results.append({
                    'name': name,
                    'score': round(score * 100, 2) if score <= 1 else round(score, 2)
                })
    except Exception as e:
        results.append({"error": f"处理过程中发生错误: {str(e)}"})
    
    return results

def detect_objects(image_path, api_url, access_token):
    """多主体检测"""
    with open(image_path, 'rb') as f:
        img = base64.b64encode(f.read())
    
    params = {"image": img}
    request_url = f"{api_url}?access_token={access_token}"
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    response = requests.post(request_url, data=params, headers=headers)
    
    if response:
        return response.json()
    return None

def recognize_ingredient(cropped_image, crop_index, api_url, access_token):
    """细粒度识别食材"""
    # 将PIL图像转为base64
    buffered = io.BytesIO()
    cropped_image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue())
    
    params = {"image": img_str}
    request_url = f"{api_url}?access_token={access_token}"
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    response = requests.post(request_url, data=params, headers=headers)
    
    if response:
        result = response.json()
        # 返回置信度最高的结果（排除"非果蔬食材"）
        for item in result.get("result", []):
            if item["name"] != "非果蔬食材":
                return item["name"], item["score"]
    return None, 0