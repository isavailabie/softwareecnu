from django.shortcuts import render, redirect
from django.http import JsonResponse

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

# Create your views here.

# 商品列表页视图
def product_list(request):
    return render(request, 'fruit/index.html', {'products': PRODUCTS})

# 加入购物车视图
def add_to_cart(request, product_id):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        cart = request.session.get('cart', {})
        product = next((p for p in PRODUCTS if p['id'] == product_id), None)
        if not product:
            return JsonResponse({'success': False})
        quantity = int(request.POST.get('quantity', 1))
        if str(product_id) in cart:
            cart[str(product_id)]['quantity'] += quantity
        else:
            cart[str(product_id)] = {
                'id': product['id'],
                'name': product['name'],
                'price': product['price'],
                'image_url': product['image_url'],
                'category': product['category'],
                'description': product['description'],
                'tag': product['tag'],
                'quantity': quantity
            }
        request.session['cart'] = cart
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=405)

def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = list(cart.values())
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render(request, 'fruit/cart.html', {'cart_items': cart_items, 'total': total})

def update_cart(request, product_id):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        quantity = int(request.POST.get('quantity', 1))
        if str(product_id) in cart:
            if quantity > 0:
                cart[str(product_id)]['quantity'] = quantity
            else:
                del cart[str(product_id)]
        request.session['cart'] = cart
    return redirect('cart_view')

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
        request.session['cart'] = cart
    return redirect('cart_view')
