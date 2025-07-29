"""Extra tests for fruit.views to raise coverage over 82%."""

import json
import datetime
from django.test import TestCase, RequestFactory, Client
from django.contrib.auth.models import User, AnonymousUser
from django.urls import reverse

from fruit import views as fv
from fruit.models import UserCalorieRecord, CartItem
from recommender.models import RecipeFlat

class RecipeViewTests(TestCase):
    databases = {"default", "recommend"}

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="chef", password="pwd12345")
        self.client.force_login(self.user)
        # popular recipes: rating field maybe exists, but just create calories
        for i in range(3):
            RecipeFlat.objects.create(
                title=f"Recipe{i}",
                calories=f"{100+i*50}kcal/100g",
                image_url="",
                rating_sum=int((5 - i * 0.5) * 10),
                category="recai",
                cook_time="20分钟",
                difficulty="简单",
                ingredients=[],
            )

    def test_recipe_view_status(self):
        resp = self.client.get(reverse("recipe_view"))
        self.assertEqual(resp.status_code, 200)
        # context keys existence
        self.assertIn("popular_recipes", resp.context)
        self.assertIn("healthy_recipes", resp.context)
        self.assertTrue(len(resp.context["popular_recipes"]) <= 10)


class RecommendRecipesTests(TestCase):
    databases = {"default", "recommend"}

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="cook", password="pwd12345")
        # candidate recipe
        RecipeFlat.objects.create(
            title="Quick Dish",
            calories="200kcal/100g",
            cook_time="10分钟",
            image_url="",
            category="recai",
            difficulty="简单",
            ingredients=[{"name": "番茄"}],
        )

    def test_recommend_recipes_basic(self):
        payload = {
            "ingredient1": "番茄",
        }
        request = self.factory.post("/recommend_recipes/", data=payload)
        request.headers = {"x-requested-with": "XMLHttpRequest"}
        request.user = self.user
        resp = fv.recommend_recipes(request)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIn("recipes", data)
        self.assertTrue(any(r["title"] == "Quick Dish" for r in data["recipes"]))


class EditCalorieRecordTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="dieter", password="pwd12345")
        self.client.force_login(self.user)
        today = datetime.date.today()
        self.record = UserCalorieRecord.objects.create(
            user=self.user,
            date=today,
            breakfast_food="粥",
            breakfast_calories=300,
            lunch_food="面",
            lunch_calories=600,
            dinner_food="米饭",
            dinner_calories=500,
            daily_target=1800,
        )

    def test_edit_calorie_record_flow(self):
        url = reverse("edit_calorie_record", args=[self.record.id])
        payload = {
            "breakfast_food": "鸡蛋",
            "breakfast_calories": "250",
            "lunch_food": "面",
            "lunch_calories": "550",
            "dinner_food": "米饭",
            "dinner_calories": "450",
        }
        resp = self.client.post(url, data=payload)
        # expect redirect back to my_view
        self.assertEqual(resp.status_code, 302)
        self.record.refresh_from_db()
        self.assertEqual(self.record.breakfast_food, "鸡蛋")
        self.assertEqual(self.record.breakfast_calories, 250)
