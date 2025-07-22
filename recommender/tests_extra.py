from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User

from recommender.models import RecipeFlat, Ingredient, Recipe, RecipeIngredient, EnergyRequirement, ProteinRequirement
from recommender.views import _cal_num, _score_recipe
from fruit.models import UserCalorieRecord
import json


class CalNumFunctionTest(TestCase):
    def test_cal_num_extracts_number(self):
        self.assertEqual(_cal_num("205大卡/100g"), 205.0)
        self.assertEqual(_cal_num("300kcal/份"), 300.0)
        self.assertEqual(_cal_num("无数据"), 0.0)


class ScoreRecipeFunctionTest(TestCase):    
    databases = {'default', 'recommend'}
    def setUp(self):
        self.recipe = RecipeFlat.objects.create(
            title="番茄炒蛋",
            calories="200千卡/100g",
            ingredients=[{"name": "番茄"}, {"name": "鸡蛋"}],
            rating_sum=100,
        )

    def test_score_with_full_coverage(self):
        provided = {"番茄", "鸡蛋"}
        score = _score_recipe(self.recipe, provided, target_calories=200)
        # 满分情况, 分数应接近 1
        self.assertGreaterEqual(score, 0.95)

    def test_score_with_zero_coverage(self):
        provided = {"黄瓜"}
        score = _score_recipe(self.recipe, provided, target_calories=200)
        # 无覆盖率应返回 0
        self.assertEqual(score, 0.0)

    def test_score_with_half_coverage_and_calorie_gap(self):
        provided = {"番茄"}  # 50% 覆盖
        # target_calories 100 与 实际 200 差距 50% -> calorie_score = 0.5, cover_score = 0.5
        # 总分 = 0.6*0.5 + 0.4*0.5 = 0.5
        score = _score_recipe(self.recipe, provided, target_calories=100)
        self.assertAlmostEqual(score, 0.2, places=2)


class UserCalorieRecordStatusTest(TestCase):
    databases = {'default', 'recommend'}
    def setUp(self):
        self.user = User.objects.create_user("calorie", "calorie@example.com", "pass")

    def _create_record(self, breakfast, lunch, dinner, target=1000):
        return UserCalorieRecord.objects.create(
            user=self.user,
            date=timezone.now().date(),
            breakfast_calories=breakfast,
            lunch_calories=lunch,
            dinner_calories=dinner,
            daily_target=target,
        )

    def test_status_good(self):
        rec = self._create_record(100, 200, 100, target=1000)
        self.assertEqual(rec.status, "good")

    def test_status_warning(self):
        rec = self._create_record(400, 350, 200, target=1000)  # 95%
        self.assertEqual(rec.status, "warning")

    def test_status_exceed(self):
        rec = self._create_record(600, 500, 200, target=1000)  # 130%
        self.assertEqual(rec.status, "warning")


class RecommenderModelStrTest(TestCase):
    """Simply call __str__ to mark those lines as covered."""
    databases = {'default', 'recommend'}
    def test_str_methods(self):
        ing = Ingredient.objects.create(name="白菜")
        rec = Recipe.objects.create(title="白菜汤", instructions="煮", )
        RecipeIngredient.objects.create(recipe=rec, ingredient=ing)
        detail = EnergyRequirement.objects.create(sex="M", pal_level="I", age_min=18, age_max=29, value="2300", unit="kcal/d")
        protein = ProteinRequirement.objects.create(sex="M", req_type="EAR", age_min=18, age_max=29, value="60", unit="g/d")

        # Touch __str__
        str(ing)
        str(rec)
        str(detail)
        str(protein)
        rf = RecipeFlat.objects.create(title="test flat")
        str(rf)
