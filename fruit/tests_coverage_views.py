"""Additional tests exercising fruit.views to raise coverage."""

import json
import datetime
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser, User
from django.urls import reverse

from fruit import views as fv
from fruit.models import CartItem

class FruitViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="buyer", password="pwd12345")

    def _post(self, view_func, url_kwargs: dict | None = None, data: dict | None = None, ajax: bool = False):
        url_kwargs = url_kwargs or {}
        data = data or {}
        request = self.factory.post("/dummy/", data=data)
        if ajax:
            request.headers = {"x-requested-with": "XMLHttpRequest"}
        request.user = self.user
        return view_func(request, **url_kwargs)

    def _get(self, view_func, url_kwargs: dict | None = None):
        url_kwargs = url_kwargs or {}
        request = self.factory.get("/dummy/")
        request.user = self.user
        return view_func(request, **url_kwargs)

    def test_product_list_requires_login(self):
        # Unauthenticated request should redirect
        req = self.factory.get("/")
        req.user = AnonymousUser()
        resp = fv.product_list(req)
        self.assertEqual(resp.status_code, 302)

        # Authenticated should render 200
        resp2 = self._get(fv.product_list)
        self.assertEqual(resp2.status_code, 200)

    def test_add_update_remove_cart_flow(self):
        # 1. Add to cart via AJAX
        resp = self._post(fv.add_to_cart, {"product_id": 1}, {"quantity": 2}, ajax=True)
        self.assertJSONEqual(resp.content, {"success": True})
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 1)

        # 2. Update cart quantity
        resp2 = self._post(fv.update_cart, {"product_id": 1}, {"quantity": 3})
        self.assertEqual(CartItem.objects.get(user=self.user).quantity, 3)

        # 3. Remove from cart (quantity 0)
        resp3 = self._post(fv.update_cart, {"product_id": 1}, {"quantity": 0})
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 0)

    def test_safe_int_helpers(self):
        safe_int = getattr(fv.my_view, "safe_int", None)
        if not safe_int:
            self.skipTest("safe_int helper not exposed; skip")
        self.assertEqual(safe_int("10"), 10)
        self.assertEqual(safe_int("abc", 5), 5)

    def test_time_and_calorie_value_helpers(self):
        # prepare fake recipe object with calories attribute
        class R: pass
        r = R(); r.calories = "205大卡/100g"
        cal_val_func = getattr(fv.recipe_view, "calorie_value", getattr(fv, "calorie_value", None))
        if not cal_val_func:
            self.skipTest("calorie_value helper not exposed; skip")
        self.assertEqual(cal_val_func(r), 205)
        self.assertEqual(fv.recommend_recipes.time_value("60分钟"), 60)
        self.assertEqual(fv.recommend_recipes.time_value(None), 10 ** 9)
