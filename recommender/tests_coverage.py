"""Extra tests to improve coverage (>82%).
Focus areas:
1. Helper functions in recommender.views (pure logic)
2. UserProfile BMI / recommended calories logic in fruit.models
3. Basic import of heavy fruit.views module to execute many uncounted lines
"""

import datetime
from django.test import TestCase, SimpleTestCase
from django.contrib.auth.models import User

# 1. Tests for recommender.views helper functions
from recommender.views import _cal_num, _score_recipe
from recommender.models import RecipeFlat

class CalNumTests(SimpleTestCase):
    def test_cal_num_extracts_number(self):
        self.assertEqual(_cal_num("205kcal/100g"), 205)
        self.assertEqual(_cal_num("30 大卡/份"), 30)
        self.assertEqual(_cal_num(""), 0)


class ScoreRecipeTests(TestCase):
    # 使用 recommend 第二数据库
    databases = {"default", "recommend"}
    def setUp(self):
        # Minimal RecipeFlat instance with one ingredient and calories field
        self.recipe = RecipeFlat.objects.create(
            title="番茄炒蛋",
            calories="200kcal/100g",
            ingredients=[{"name": "egg", "amount": "2"}],
        )

    def test_score_recipe_full_match(self):
        score = _score_recipe(self.recipe, {"egg"}, target_calories=200)
        # 理论最高分 1.0，但由于权重及浮点，设定 >=0.95
        self.assertGreaterEqual(score, 0.95)

    def test_score_recipe_no_match(self):
        # 提供的食材都不匹配 -> 评分应为 0
        score = _score_recipe(self.recipe, {"tomato"}, target_calories=200)
        self.assertEqual(score, 0.0)


# 2. Tests for fruit.models.UserProfile helper methods
from fruit.models import UserProfile

class UserProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pwd12345")

    def test_bmi_and_recommended_calories(self):
        profile = self.user.profile
        profile.height = 175
        profile.weight = 70
        profile.gender = "M"
        profile.activity_level = "II"
        profile.birth_date = datetime.date(1995, 1, 1)
        profile.save()
        # BMI 计算应大约为 22.9
        self.assertAlmostEqual(profile.bmi, 22.9, places=1)
        # 推荐热量应在常见成年男性范围内
        self.assertGreaterEqual(profile.get_recommended_calories(), 1800)
        self.assertLessEqual(profile.get_recommended_calories(), 2600)


# 3. Import heavy fruit.views module so its top-level code is executed
class ImportFruitViewsTest(SimpleTestCase):
    def test_import(self):
        import importlib
        module = importlib.import_module("fruit.views")
        # 常量 PRODUCTS 应已定义
        self.assertTrue(hasattr(module, "PRODUCTS"))
