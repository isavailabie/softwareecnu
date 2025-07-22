from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User

from fruit.models import UserProfile
from recommender.models import RecipeFlat


class UserProfileCalorieRecommendationEdgeCaseTest(TestCase):
    """Cover the branch logic inside UserProfile.get_recommended_calories for
    (1) 极低 BMI 导致增加热量, (2) 超高 BMI 导致减少热量。"""

    def setUp(self):
        self.user = User.objects.create_user(username="edgecase", password="pass123")
        self.profile: UserProfile = self.user.profile
        self.profile.height = 170  # cm
        self.profile.gender = "M"
        self.profile.activity_level = "III"  # 高活动度, base=2600
        # 30 岁
        self.profile.birth_date = timezone.now().date().replace(year=timezone.now().year - 30)

    def test_underweight_increases_recommendation(self):
        # BMI ≈ 17.3 (<18.5) 应触发 +200
        self.profile.weight = 50  # kg
        self.profile.save()
        recommended = self.profile.get_recommended_calories()
        self.assertGreaterEqual(recommended, 2600 + 200)

    def test_overweight_decreases_recommendation(self):
        # BMI ≈ 34.6 (>25) 应触发 -200
        self.profile.weight = 100  # kg
        self.profile.save()
        recommended = self.profile.get_recommended_calories()
        self.assertLessEqual(recommended, 2600 - 200)


class RecipeViewContextTest(TestCase):
    """验证 recipe_view 选择热门菜谱和健康菜谱的逻辑是否正确。"""
    databases = {'default', 'recommend'}
    def setUp(self):
        self.user = User.objects.create_user(username="viewer", password="pass123")
        self.client.login(username="viewer", password="pass123")

        # 创建 5 条 RecipeFlat, 手动设置 rating_sum 和 calories
        data = [
            ("A", 500, "100大卡/100g"),  # 高评分, 低热量
            ("B", 400, "200大卡/100g"),
            ("C", 300, "50大卡/100g"),   # 低热量
            ("D", 200, "1000大卡/100g"),
            ("E", 100, "")               # 无热量
        ]
        for title, rating, cal in data:
            RecipeFlat.objects.create(title=title, rating_sum=rating, calories=cal)

    def test_recipe_view_popular_and_healthy(self):
        response = self.client.get(reverse("recipe_view"))
        self.assertEqual(response.status_code, 200)
        popular = list(response.context["popular_recipes"])
        healthy = list(response.context["healthy_recipes"])

        # popular 应按 rating_sum 降序排前 3 条 (A,B,C)
        self.assertEqual([r.title for r in popular], ["A", "B", "C"])
        # healthy 应按 calorie_value 升序排前 3 条 (C,A,B)
        self.assertEqual([r.title for r in healthy], ["C", "A", "B"])
