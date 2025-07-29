"""Extra unit tests for recommender.views to raise coverage."""

import json
import datetime
from unittest import mock

from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.http import HttpRequest

from recommender import views as rv
from recommender.models import RecipeFlat, EnergyRequirement


class RecommendViewTests(TestCase):
    # need secondary DB alias
    databases = {"default", "recommend"}

    def setUp(self):
        self.factory = RequestFactory()
        # Minimal EnergyRequirement so calorie computation uses real data
        EnergyRequirement.objects.using("recommend").create(
            sex="M",
            pal_level="II",
            age_min=18,
            age_max=45,
            value="2000kcal",
        )
        # Recipe that matches provided ingredients
        RecipeFlat.objects.using("recommend").create(
            title="番茄炒蛋",
            image_url="",
            calories="300kcal/100g",
            category="recai",
            cook_time="15分钟",
            difficulty="简单",
            ingredients=[{"name": "番茄"}, {"name": "鸡蛋"}],
        )

    def _post_json(self, body: dict) -> HttpRequest:
        req = self.factory.post(
            "/recommender/recommend/",
            data=json.dumps(body).encode(),
            content_type="application/json",
        )
        return req

    def test_invalid_json(self):
        request = self.factory.post("/recommender/recommend/", data=b"not-json", content_type="application/json")
        resp = rv.recommend_view(request)
        self.assertEqual(resp.status_code, 400)


    def test_basic_recommend_flow(self):
        body = {
            "available_ingredients": ["番茄", "鸡蛋"],
            "physical_data": [{"age": 30, "sex": "M", "activity_level": "moderate"}],
            "history": [],
        }
        request = self._post_json(body)
        resp = rv.recommend_view(request)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        # Expect combos list present even if might be empty
        self.assertIn("combos", data)
    def test_get_ai_combos_no_key(self):
        if not hasattr(rv, "_get_ai_combos"):
            self.skipTest("_get_ai_combos not exposed; skip")
        with mock.patch.dict("os.environ", {}, clear=True):
            combos = rv._get_ai_combos(["tomato"], 500)
            self.assertEqual(combos, [])
