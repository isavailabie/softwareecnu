from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class UserProfile(models.Model):
    """用户个人信息扩展"""
    GENDER_CHOICES = [
        ('M', '男'),
        ('F', '女'),
    ]
    
    ACTIVITY_CHOICES = [
        ('I', '低活动度（久坐少动）'),
        ('II', '中活动度（日常活动）'),
        ('III', '高活动度（经常运动）'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    height = models.PositiveSmallIntegerField(null=True, blank=True, help_text='身高（厘米）')
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text='体重（公斤）')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    activity_level = models.CharField(max_length=5, choices=ACTIVITY_CHOICES, default='II')
    birth_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}的个人资料"
    
    @property
    def age(self):
        if not self.birth_date:
            return None
        today = timezone.now().date()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
    
    @property
    def bmi(self):
        if not self.height or not self.weight:
            return None
        height_m = self.height / 100
        return round(float(self.weight) / (height_m * height_m), 1)
    
    def get_recommended_calories(self):
        """获取推荐热量摄入"""
        if not self.gender or not self.activity_level or not self.age:
            return 1500  # 默认值
        
        # 基于性别、活动等级和年龄计算推荐热量
        # 简化版本的计算方法
        if self.gender == 'M':
            base = 1800
            if self.activity_level == 'I':
                base = 1800
            elif self.activity_level == 'II':
                base = 2200
            else:  # 'III'
                base = 2600
        else:  # 'F'
            base = 1500
            if self.activity_level == 'I':
                base = 1500
            elif self.activity_level == 'II':
                base = 1800
            else:  # 'III'
                base = 2100
        
        # 年龄调整
        if self.age < 18:
            base += 200
        elif self.age > 50:
            base -= 200
            
        # 如果有体重，可以进一步调整
        if self.weight:
            # 体重偏低，增加热量
            if self.bmi and self.bmi < 18.5:
                base += 200
            # 体重偏高，减少热量
            elif self.bmi and self.bmi > 25:
                base -= 200
                
        return base

# 当创建User时自动创建UserProfile
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if not hasattr(instance, 'profile'):
        UserProfile.objects.create(user=instance)
    instance.profile.save()

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

class UserCalorieRecord(models.Model):
    """用户每日热量记录"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calorie_records')
    date = models.DateField(default=timezone.now)
    
    breakfast_food = models.CharField(max_length=200, blank=True)
    breakfast_calories = models.IntegerField(default=0)
    
    lunch_food = models.CharField(max_length=200, blank=True)
    lunch_calories = models.IntegerField(default=0)
    
    dinner_food = models.CharField(max_length=200, blank=True)
    dinner_calories = models.IntegerField(default=0)
    
    daily_target = models.IntegerField(default=1500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date']
        
    def __str__(self):
        return f"{self.user.username} - {self.date}"
    
    @property
    def total_calories(self):
        return self.breakfast_calories + self.lunch_calories + self.dinner_calories
    
    @property
    def remaining_calories(self):
        return max(0, self.daily_target - self.total_calories)
    
    @property
    def completion_percentage(self):
        return min(100, int((self.total_calories / self.daily_target) * 100))
    
    @property
    def status(self):
        percentage = self.completion_percentage
        if percentage > 100:
            return 'exceed'  # 超标
        elif percentage > 90:
            return 'warning'  # 接近上限
        else:
            return 'good'  # 达标

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
