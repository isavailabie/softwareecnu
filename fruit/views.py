from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import CartItem, Recipe, Ingredient, RecipeIngredient

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
def my_view(request):
    if not request.user.is_authenticated:
        return redirect('login_view')
    
    return render(request, 'fruit/my.html')

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
        
        # 查找包含这些食材的菜谱
        matching_recipes = []
        all_recipes = Recipe.objects.all()
        
        for recipe in all_recipes:
            recipe_ingredients = RecipeIngredient.objects.filter(recipe=recipe)
            recipe_ingredient_names = [ri.ingredient.name for ri in recipe_ingredients]
            
            # 计算匹配度
            matched_ingredients = set(ingredients) & set(recipe_ingredient_names)
            match_percentage = len(matched_ingredients) / len(recipe_ingredient_names) * 100
            
            # 检查是否需要额外食材
            needs_extra = len(matched_ingredients) < len(recipe_ingredient_names)
            
            if matched_ingredients:  # 至少匹配一种食材
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
                
                # 添加食材信息
                for ri in recipe_ingredients:
                    ingredient_data = {
                        'name': ri.ingredient.name,
                        'amount': ri.amount,
                        'is_match': ri.ingredient.name in matched_ingredients
                    }
                    recipe_data['ingredients'].append(ingredient_data)
                
                matching_recipes.append(recipe_data)
        
        # 按匹配度排序
        matching_recipes.sort(key=lambda x: x['match_percentage'], reverse=True)
        
        return JsonResponse({'success': True, 'recipes': matching_recipes})
    
    return JsonResponse({'success': False, 'message': '请求方法不正确'})

# 菜谱详情页
@login_required
def recipe_detail(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    recipe_ingredients = RecipeIngredient.objects.filter(recipe=recipe)
    
    # 将烹饪步骤拆分为列表
    steps = []
    for i, step_text in enumerate(recipe.steps.split('\n')):
        if step_text.strip():
            step = {
                'number': i + 1,
                'title': f"步骤 {i + 1}",
                'description': step_text.strip(),
                'tip': ''
            }
            steps.append(step)
    
    # 准备营养信息
    nutrition = [
        {'value': recipe.calories.replace('大卡', '').replace('千卡', '') if recipe.calories else '0', 'label': '卡路里'},
        {'value': recipe.protein, 'label': '蛋白质'},
        {'value': recipe.fat, 'label': '脂肪'},
        {'value': recipe.carbohydrates, 'label': '碳水化合物'}
    ]
    
    # 准备小贴士
    tips = [
        {
            'title': '选材技巧',
            'content': f'选择新鲜的食材，特别是{", ".join([ri.ingredient.name for ri in recipe_ingredients[:2]])}等主要食材，以保证菜品的口感和营养。'
        },
        {
            'title': '火候控制',
            'content': '根据食材的特性调整火候，保持食材的最佳口感和营养。'
        },
        {
            'title': '调味秘诀',
            'content': '调味料要适量，先尝后调，循序渐进地添加调味料，以免过咸或过淡。'
        },
        {
            'title': '营养搭配',
            'content': f'这道菜富含{recipe.protein}蛋白质和{recipe.carbohydrates}碳水化合物，是很好的营养搭配。'
        }
    ]
    
    context = {
        'recipe': recipe,
        'ingredients': recipe_ingredients,
        'steps': steps,
        'nutrition': nutrition,
        'tips': tips,
        'match_percentage': request.GET.get('match', '100%')
    }
    
    return render(request, 'fruit/recipe_detail.html', context)
