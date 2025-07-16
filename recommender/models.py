from django.db import models

class Ingredient(models.Model):
    """单一食材表，保证全局唯一名称。"""
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """菜谱表。"""
    title = models.CharField(max_length=100)
    instructions = models.TextField(blank=True)
    ingredients = models.ManyToManyField(Ingredient, through="RecipeIngredient")

    def __str__(self):
        return self.title




class EnergyRequirement(models.Model):
    """能量(热量)推荐摄入量表，按 PAL 分级"""
    SEX_CHOICES = [("M", "male"), ("F", "female")]
    PAL_CHOICES = [("I", "PAL I"), ("II", "PAL II"), ("III", "PAL III")]

    sex = models.CharField(max_length=1, choices=SEX_CHOICES)
    pal_level = models.CharField(max_length=4, choices=PAL_CHOICES)
    age_min = models.PositiveSmallIntegerField()
    age_max = models.PositiveSmallIntegerField()
    value = models.CharField(max_length=20)  # 支持定量和按体重
    unit = models.CharField(max_length=20)   # kcal/d 或 kcal/(kg·d)

    class Meta:
        unique_together = ("sex", "pal_level", "age_min")
        ordering = ["sex", "pal_level", "age_min"]

    def __str__(self):
        return f"{self.get_sex_display()} PAL{self.pal_level} {self.age_min}-{self.age_max}: {self.value}{self.unit}"


class ProteinRequirement(models.Model):
    """蛋白质推荐摄入量（EAR/RNI/AMDR）表。统一存放男女不同年龄段的参考值。"""

    SEX_CHOICES = [("M", "male"), ("F", "female")]
    TYPE_CHOICES = [("EAR", "EAR"), ("RNI", "RNI"), ("AMDR", "AMDR")]

    sex = models.CharField(max_length=1, choices=SEX_CHOICES)
    req_type = models.CharField(max_length=4, choices=TYPE_CHOICES)
    age_min = models.PositiveSmallIntegerField(help_text="起始年龄，单位: 岁")
    age_max = models.PositiveSmallIntegerField(help_text="终止年龄，单位: 岁")
    value = models.CharField(max_length=20, help_text="定量或区间数值，如 '60' 或 '8-20'")
    unit = models.CharField(max_length=10, help_text="单位，如 g/d 或 %E")

    class Meta:
        unique_together = ("sex", "req_type", "age_min")
        ordering = ["sex", "req_type", "age_min"]

    def __str__(self):
        return f"{self.get_sex_display()} {self.req_type} {self.age_min}-{self.age_max}: {self.value}{self.unit}"



class RecipeDetail(models.Model):
    """菜谱详情表，存储图片、营养等附加信息。"""
    recipe = models.OneToOneField(Recipe, on_delete=models.CASCADE, related_name="detail")
    image_url = models.URLField(blank=True)
    image_path = models.CharField(max_length=200, blank=True)
    calories = models.CharField(max_length=50, blank=True)
    nutrition = models.JSONField(blank=True, null=True)
    description = models.TextField(blank=True)
    cook_time = models.CharField(max_length=50, blank=True)
    difficulty = models.CharField(max_length=20, blank=True)
    category = models.CharField(max_length=50, blank=True)  # 类型/标签
    servings = models.CharField(max_length=20, blank=True)
    steps = models.JSONField(blank=True, null=True)
    rating_sum = models.PositiveIntegerField(default=4)
    rating_count = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.recipe.title} - detail"


class RecipeFlat(models.Model):
    """Denormalized recipe table storing all fields in one row."""
    title = models.CharField(max_length=100, unique=True)
    image_url = models.URLField(blank=True)
    image_path = models.CharField(max_length=200, blank=True)
    calories = models.CharField(max_length=50, blank=True)
    nutrition = models.JSONField(blank=True, null=True)
    description = models.TextField(blank=True)
    cook_time = models.CharField(max_length=50, blank=True)
    difficulty = models.CharField(max_length=20, blank=True)
    category = models.CharField(max_length=50, blank=True)
    servings = models.CharField(max_length=20, blank=True)
    steps = models.JSONField(blank=True, null=True)
    ingredients = models.JSONField(blank=True, null=True)  # list of {name, amount}
    rating_sum = models.PositiveIntegerField(default=4)
    rating_count = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.title


class TempRecipeFlat(models.Model):
    """Temporary duplicate of RecipeFlat with identical schema."""
    title = models.CharField(max_length=100, unique=True)
    image_url = models.URLField(blank=True)
    image_path = models.CharField(max_length=200, blank=True)
    calories = models.CharField(max_length=50, blank=True)
    nutrition = models.JSONField(blank=True, null=True)
    description = models.TextField(blank=True)
    cook_time = models.CharField(max_length=50, blank=True)
    difficulty = models.CharField(max_length=20, blank=True)
    category = models.CharField(max_length=50, blank=True)
    servings = models.CharField(max_length=20, blank=True)
    steps = models.JSONField(blank=True, null=True)
    ingredients = models.JSONField(blank=True, null=True)
    rating_sum = models.PositiveIntegerField(default=4)
    rating_count = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "temp_recommender_recipeflat"

    def __str__(self):
        return self.title


class RecipeIngredient(models.Model):
    """菜谱与食材的多对多关系表。"""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.CharField(max_length=30, blank=True)

    class Meta:
        unique_together = ("recipe", "ingredient")

    def __str__(self):
        return f"{self.recipe.title} - {self.ingredient.name}"
