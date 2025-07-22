from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from .models import CartItem, Recipe, Ingredient, RecipeIngredient, FavoriteIngredient, FridgeItem, UserCalorieRecord, UserProfile
import json
from django.utils import timezone

# ========== fruit 应用相关测试 ==========

class UserAuthenticationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_user_login(self):
        response = self.client.post(reverse('login_view'), {'username': 'testuser', 'password': 'testpass'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse('product_list')))

    def test_user_register(self):
        response = self.client.post(reverse('register_view'), {'username': 'newuser', 'password': 'newpass'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse('product_list')))

    def test_user_logout(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('logout_view'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse('login_view')))

class CartTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')
        self.product_id = 1
        self.product_price = 19.99

    def test_add_to_cart(self):
        response = self.client.post(
            reverse('add_to_cart', args=[self.product_id]),
            {'quantity': 1},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get('success'), True)

    def test_update_cart(self):
        CartItem.objects.create(
            user=self.user,
            product_id=self.product_id,
            quantity=1,
            price=self.product_price
        )
        response = self.client.post(
            reverse('update_cart', args=[self.product_id]),
            {'quantity': 2}
        )
        self.assertEqual(response.status_code, 302)
        cart_item = CartItem.objects.get(user=self.user, product_id=self.product_id)
        self.assertEqual(cart_item.quantity, 2)

    def test_remove_from_cart(self):
        CartItem.objects.create(
            user=self.user,
            product_id=self.product_id,
            quantity=1,
            price=self.product_price
        )
        response = self.client.get(reverse('remove_from_cart', args=[self.product_id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CartItem.objects.filter(user=self.user, product_id=self.product_id).count(), 0)

class FavoriteIngredientTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')
        self.ingredient_name = 'Apple'

    def test_toggle_favorite_ingredient(self):
        response = self.client.post(reverse('toggle_favorite_ingredient'), {'name': self.ingredient_name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get('success'), True)
        self.assertEqual(response.json().get('is_favorited'), True)
        response = self.client.post(reverse('toggle_favorite_ingredient'), {'name': self.ingredient_name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get('success'), True)
        self.assertEqual(response.json().get('is_favorited'), False)

    def test_check_favorite_status(self):
        FavoriteIngredient.objects.create(user=self.user, name=self.ingredient_name)
        response = self.client.get(reverse('check_favorite_status'), {'name': self.ingredient_name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get('success'), True)
        self.assertEqual(response.json().get('is_favorited'), True)

class FridgeTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')
        self.ingredient_name = 'Banana'

    def test_add_to_fridge(self):
        response = self.client.post(reverse('add_to_fridge'), {'name': self.ingredient_name, 'quantity': 2, 'source': 'manual'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get('success'), True)
        self.assertEqual(FridgeItem.objects.filter(user=self.user, name=self.ingredient_name).count(), 1)

    def test_fridge_view(self):
        FridgeItem.objects.create(user=self.user, name=self.ingredient_name, quantity=1, source='manual')
        response = self.client.get(reverse('fridge_view'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.ingredient_name)

class UserProfileModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='profileuser', password='testpass')
        self.profile = UserProfile.objects.get(user=self.user)

    def test_profile_auto_created(self):
        self.assertIsNotNone(self.profile)
        self.assertEqual(self.profile.user, self.user)

    def test_age_and_bmi(self):
        self.profile.height = 170
        self.profile.weight = 65
        self.profile.birth_date = timezone.now().date().replace(year=timezone.now().year - 25)
        self.profile.save()
        self.assertEqual(self.profile.age, 25)
        self.assertAlmostEqual(self.profile.bmi, 22.5, places=1)

    def test_get_recommended_calories(self):
        self.profile.height = 170
        self.profile.weight = 50
        self.profile.gender = 'F'
        self.profile.activity_level = 'II'
        self.profile.birth_date = timezone.now().date().replace(year=timezone.now().year - 30)
        self.profile.save()
        cal = self.profile.get_recommended_calories()
        self.assertIsInstance(cal, int)
        self.assertGreater(cal, 0)

class UserCalorieRecordModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='calorieuser', password='testpass')
        self.record = UserCalorieRecord.objects.create(
            user=self.user,
            date=timezone.now().date(),
            breakfast_calories=200,
            lunch_calories=400,
            dinner_calories=500,
            daily_target=1200
        )

    def test_total_and_remaining_calories(self):
        self.assertEqual(self.record.total_calories, 1100)
        self.assertEqual(self.record.remaining_calories, 100)
        self.assertEqual(self.record.completion_percentage, 91)
        self.assertEqual(self.record.status, 'warning')

    def test_unique_constraint(self):
        with self.assertRaises(Exception):
            UserCalorieRecord.objects.create(user=self.user, date=self.record.date)

class RecipeAndIngredientModelTestCase(TestCase):
    def setUp(self):
        self.ingredient1 = Ingredient.objects.create(name='土豆')
        self.ingredient2 = Ingredient.objects.create(name='胡萝卜')
        self.recipe = Recipe.objects.create(
            title='土豆炖胡萝卜',
            cooking_time=40,
            difficulty='中等',
            image_url='test.jpg',
            steps='1. 切土豆\n2. 切胡萝卜',
            is_popular=True,
            is_healthy=True
        )
        RecipeIngredient.objects.create(recipe=self.recipe, ingredient=self.ingredient1, amount='200g', is_main=True)
        RecipeIngredient.objects.create(recipe=self.recipe, ingredient=self.ingredient2, amount='100g', is_main=False)
        self.recipe.ingredients.add(self.ingredient1, self.ingredient2)

    def test_recipe_str(self):
        self.assertIn('土豆炖胡萝卜', str(self.recipe))

    def test_ingredient_unique(self):
        with self.assertRaises(Exception):
            Ingredient.objects.create(name='土豆')

    def test_recipe_ingredient_unique(self):
        with self.assertRaises(Exception):
            RecipeIngredient.objects.create(recipe=self.recipe, ingredient=self.ingredient1, amount='100g')

class FridgeItemViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='fridgeuser', password='testpass')
        self.client.login(username='fridgeuser', password='testpass')
        self.item = FridgeItem.objects.create(user=self.user, name='西红柿', quantity=2, source='manual')

    def test_update_fridge_item(self):
        url = reverse('update_fridge_item', args=[self.item.id])
        response = self.client.post(url, {'name': '西红柿', 'quantity': 5})
        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 5)

    def test_delete_fridge_item(self):
        url = reverse('delete_fridge_item', args=[self.item.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(FridgeItem.objects.filter(id=self.item.id).exists())

    def test_update_fridge_item_not_exist(self):
        url = reverse('update_fridge_item', args=[9999])
        response = self.client.post(url, {'name': '不存在', 'quantity': 1})
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.json())

    def test_delete_fridge_item_not_exist(self):
        url = reverse('delete_fridge_item', args=[9999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.json())

class MyViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='myviewuser', password='testpass')
        self.client.login(username='myviewuser', password='testpass')

    def test_get_my_view(self):
        response = self.client.get(reverse('my_view'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('个人', response.content.decode() or 'my')

    def test_update_profile(self):
        data = {
            'update_profile': '1',
            'height': 180,
            'weight': 70,
            'gender': 'M',
            'activity_level': 'II',
            'birth_date': '2000-01-01',
        }
        response = self.client.post(reverse('my_view'), data)
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.height, 180)
        self.assertEqual(str(self.user.profile.birth_date), '2000-01-01')

    def test_update_profile_invalid_birth(self):
        data = {
            'update_profile': '1',
            'height': 180,
            'weight': 70,
            'gender': 'M',
            'activity_level': 'II',
            'birth_date': 'invalid-date',
        }
        response = self.client.post(reverse('my_view'), data)
        self.assertEqual(response.status_code, 302)

    def test_calorie_record_post(self):
        data = {
            'breakfast_food': '鸡蛋',
            'breakfast_calories': 100,
            'lunch_food': '米饭',
            'lunch_calories': 300,
            'dinner_food': '面条',
            'dinner_calories': 400,
        }
        response = self.client.post(reverse('my_view'), data)
        self.assertEqual(response.status_code, 302)
        record = UserCalorieRecord.objects.get(user=self.user, date=timezone.now().date())
        self.assertEqual(record.breakfast_food, '鸡蛋')
        self.assertEqual(record.lunch_calories, 300)
        self.assertEqual(record.dinner_calories, 400)

# ========== recommender 推荐系统相关测试 ==========
from types import SimpleNamespace
from recommender.views import _score_recipe, recommend_view
import re
def _cal_num(cal_str: str) -> float:
    m = re.search(r"(\d+)", cal_str or "")
    return float(m.group(1)) if m else 0.0
from recommender.models import RecipeFlat
from unittest.mock import patch
from django.utils import timezone as dj_timezone
from datetime import datetime

class ScoreRecipeTests(TestCase):
    def test_score_recipe_basic(self):
        recipe = SimpleNamespace(
            calories="500 kcal",
            ingredients=[{"name": "tomato"}, {"name": "egg"}],
        )
        score = _score_recipe(recipe, {"tomato", "egg"}, target_calories=500)
        self.assertGreaterEqual(score, 0.9)

    def test_score_recipe_no_ingredients(self):
        recipe = SimpleNamespace(calories="300 kcal", ingredients=[])
        score = _score_recipe(recipe, set(), target_calories=300)
        self.assertEqual(score, 0.0)

class CalorieParseTests(TestCase):
    def test_parses_plain_number(self):
        self.assertEqual(_cal_num("200"), 200)
    def test_parses_with_units(self):
        self.assertEqual(_cal_num("≈150千卡"), 150)
        self.assertEqual(_cal_num("75 kcal/100g"), 75)
    def test_unknown_returns_zero(self):
        self.assertEqual(_cal_num("未知"), 0)

class RecommendViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
    def test_invalid_json_returns_400(self):
        request = self.factory.post(
            "/recommender/recommend/",
            data="{this is not valid json}",
            content_type="application/json",
        )
        response = recommend_view(request)
        self.assertEqual(response.status_code, 400)

class RecommendViewIntegrationTests(TestCase):
    databases = {"default", "recommend"}
    def setUp(self):
        self.factory = RequestFactory()
        RecipeFlat.objects.create(
            title="番茄炒蛋",
            calories="500",
            category="recai",
            ingredients=[{"name": "番茄"}, {"name": "鸡蛋"}],
            cook_time="15分钟",
            difficulty="简单"
        )
        RecipeFlat.objects.create(
            title="紫菜蛋汤",
            calories="50",
            category="tanggeng",
            ingredients=[{"name": "紫菜"}, {"name": "鸡蛋"}],
            cook_time="10分钟",
            difficulty="简单"
        )
        RecipeFlat.objects.create(
            title="拍黄瓜",
            calories="100",
            category="liangcai",
            ingredients=[{"name": "黄瓜"}],
            cook_time="5分钟",
            difficulty="简单"
        )
    def _post(self, body_dict):
        return self.factory.post(
            "/recommender/recommend/",
            data=json.dumps(body_dict),
            content_type="application/json",
        )
    @patch.dict("os.environ", {"CHATECNU_API_KEY": "test_key"})
    @patch("recommender.views.RecipeFlat.objects.using")
    @patch("recommender.views.timezone.localtime")
    def test_recommend_view_basic(self, mock_localtime, mock_using, *args):
        mock_localtime.return_value = dj_timezone.make_aware(
            datetime(2025, 7, 22, 8, 0, 0),
            timezone=dj_timezone.get_current_timezone()
        )
        mock_using.return_value = RecipeFlat.objects
        payload = {
            "available_ingredients": ["番茄", "鸡蛋"],
            "physical_data": [{
                "age": 30,
                "sex": "M",
                "activity_level": "moderate"
            }],
            "history": [],
        }
        request = self._post(payload)
        response = recommend_view(request)
        self.assertEqual(response.status_code, 200)

class ModelStrAndMetaTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='modeluser', password='testpass')
        self.profile = UserProfile.objects.get(user=self.user)
        self.ingredient = Ingredient.objects.create(name='胡萝卜')
        self.recipe = Recipe.objects.create(
            title='胡萝卜炒蛋',
            cooking_time=10,
            difficulty='简单',
            image_url='img.jpg',
            steps='1. 切胡萝卜\n2. 炒蛋',
            is_popular=False,
            is_healthy=True
        )
        self.recipe_ingredient = RecipeIngredient.objects.create(recipe=self.recipe, ingredient=self.ingredient, amount='100g', is_main=True)
        self.favorite = FavoriteIngredient.objects.create(user=self.user, name='胡萝卜')
        self.fridge_item = FridgeItem.objects.create(user=self.user, name='胡萝卜', quantity=2, source='manual')
        self.calorie_record = UserCalorieRecord.objects.create(user=self.user, date=timezone.now().date(), breakfast_calories=100, lunch_calories=200, dinner_calories=300)

    def test_userprofile_str(self):
        self.assertIn(self.user.username, str(self.profile))

    def test_userprofile_age_bmi(self):
        self.profile.height = 160
        self.profile.weight = 50
        self.profile.birth_date = timezone.now().date().replace(year=timezone.now().year - 20)
        self.profile.save()
        self.assertTrue(self.profile.age > 0)
        self.assertTrue(self.profile.bmi > 0)

    def test_userprofile_get_recommended_calories(self):
        self.profile.height = 160
        self.profile.weight = 50
        self.profile.gender = 'F'
        self.profile.activity_level = 'II'
        self.profile.birth_date = timezone.now().date().replace(year=timezone.now().year - 20)
        self.profile.save()
        self.assertTrue(self.profile.get_recommended_calories() > 0)

    def test_cartitem_str(self):
        cart = CartItem.objects.create(user=self.user, product_id=2, name='苹果', price=10, image_url='a.jpg', category='水果', description='desc', tag='', quantity=1)
        self.assertIn('苹果', str(cart))

    def test_usercalorierecord_properties(self):
        self.assertEqual(self.calorie_record.total_calories, 600)
        self.assertEqual(self.calorie_record.remaining_calories, 900)
        self.assertIn(self.calorie_record.status, ['good', 'warning', 'exceed'])
        self.assertIsInstance(self.calorie_record.completion_percentage, int)

    def test_ingredient_str(self):
        self.assertEqual(str(self.ingredient), '胡萝卜')

    def test_recipe_str(self):
        self.assertIn('胡萝卜炒蛋', str(self.recipe))

    def test_recipeingredient_str(self):
        self.assertIn('胡萝卜', str(self.recipe_ingredient))

    def test_favoriteingredient_str(self):
        self.assertIn('胡萝卜', str(self.favorite))

    def test_fridgeitem_str(self):
        self.assertIn('胡萝卜', str(self.fridge_item))

    def test_favoriteingredient_unique(self):
        with self.assertRaises(Exception):
            FavoriteIngredient.objects.create(user=self.user, name='胡萝卜')

    def test_fridgeitem_unique(self):
        with self.assertRaises(Exception):
            FridgeItem.objects.create(user=self.user, name='胡萝卜', source='manual')

    def test_recipeingredient_unique(self):
        with self.assertRaises(Exception):
            RecipeIngredient.objects.create(recipe=self.recipe, ingredient=self.ingredient, amount='50g')
