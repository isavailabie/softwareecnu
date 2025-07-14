from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product_id = models.IntegerField()
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.CharField(max_length=200)
    category = models.CharField(max_length=50)
    description = models.TextField()
    tag = models.CharField(max_length=50, blank=True)
    quantity = models.IntegerField(default=1)
    
    class Meta:
        unique_together = ('user', 'product_id')
    
    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.quantity})"

class Ingredient(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

class Recipe(models.Model):
    DIFFICULTY_CHOICES = [
        ('简单', '简单'),
        ('中等', '中等'),
        ('困难', '困难'),
    ]
    
    title = models.CharField(max_length=100)
    cooking_time = models.IntegerField(help_text='烹饪时间（分钟）', default=30)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    image_url = models.CharField(max_length=200)
    ingredients = models.ManyToManyField(Ingredient, through='RecipeIngredient')
    steps = models.TextField(help_text='烹饪步骤，每步用换行符分隔')
    is_popular = models.BooleanField(default=False)
    is_healthy = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    servings = models.CharField(max_length=50, default='2-3人份')
    calories = models.CharField(max_length=50, blank=True)
    protein = models.CharField(max_length=50, blank=True)
    fat = models.CharField(max_length=50, blank=True)
    carbohydrates = models.CharField(max_length=50, blank=True)
    fiber = models.CharField(max_length=50, blank=True)
    sodium = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return self.title

class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.CharField(max_length=50)
    is_main = models.BooleanField(default=False, help_text='是否为主要食材')
    
    class Meta:
        unique_together = ('recipe', 'ingredient')
    
    def __str__(self):
        return f"{self.recipe.title} - {self.ingredient.name} ({self.amount})"


class FavoriteIngredient(models.Model):
    """用户收藏的食材"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_ingredients')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'name')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.name}"


class FridgeItem(models.Model):
    """用户冰箱中的实际食材，可来源于识别结果 / 购物车 / 手动添加"""
    SOURCE_CHOICES = [
        ('recognized', '识别'),
        ('cart', '购物车'),
        ('manual', '手动'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fridge_items')
    name = models.CharField(max_length=100)
    quantity = models.IntegerField(default=1)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='recognized')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'name', 'source')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.quantity})"
