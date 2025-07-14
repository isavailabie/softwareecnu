from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart_view'),
    path('update_cart/<int:product_id>/', views.update_cart, name='update_cart'),
    path('remove_from_cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('my/', views.my_view, name='my_view'),
    path('login/', views.login_view, name='login_view'),
    path('register/', views.register_view, name='register_view'),
    path('logout/', views.logout_view, name='logout_view'),
    path('recipe/', views.recipe_view, name='recipe_view'),
    path('recommend_recipes/', views.recommend_recipes, name='recommend_recipes'),
    path('recipe/<int:recipe_id>/', views.recipe_detail, name='recipe_detail'),
    path('fridge/', views.recognize_fruit, name='recognize_fruit'),
    path('toggle-favorite/', views.toggle_favorite_ingredient, name='toggle_favorite_ingredient'),
    path('check-favorite/', views.check_favorite_status, name='check_favorite_status'),
    path('add-to-fridge/', views.add_to_fridge, name='add_to_fridge'),
    path('my-fridge/', views.fridge_view, name='fridge_view'),
]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)