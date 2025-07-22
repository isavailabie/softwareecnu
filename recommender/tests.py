"""Unit tests for the `recommender` module.

Only lightweight, dependency-free parts are covered here to keep the test
suite fast and isolated:

1. `_score_recipe` – scoring logic given a pseudo `RecipeFlat` instance.
2. `recommend_view._cal_num` – calorie string parser used by the view.
3. `recommend_view` – minimal negative-path test to ensure invalid JSON is
   handled gracefully (status 400).

The main view integrates heavily with the database and external services; full
integration tests should live in a separate test module with fixtures and
mocks.  These unit tests still give us confidence that the core business rules
behave as expected.
"""

from types import SimpleNamespace
from django.test import TestCase, RequestFactory

from .views import _score_recipe, recommend_view, _cal_num


class ScoreRecipeTests(TestCase):
    """Tests for the `_score_recipe` helper."""

    def test_score_recipe_basic(self):
        """Recipe close to target calories and fully covered ingredients → high score."""
        recipe = SimpleNamespace(
            calories="500 kcal",
            ingredients=[{"name": "tomato"}, {"name": "egg"}],
        )
        score = _score_recipe(recipe, {"tomato", "egg"}, target_calories=500)
        # Expect a nearly perfect score (>0.9)
        self.assertGreaterEqual(score, 0.9)

    def test_score_recipe_no_ingredients(self):
        """Recipes with 0 % coverage are disqualified (score == 0)."""
        recipe = SimpleNamespace(calories="300 kcal", ingredients=[])
        score = _score_recipe(recipe, set(), target_calories=300)
        self.assertEqual(score, 0.0)


class CalorieParseTests(TestCase):
    """Tests for `recommend_view._cal_num`."""



    def test_parses_plain_number(self):
        self.assertEqual(_cal_num("200"), 200)

    def test_parses_with_units(self):
        self.assertEqual(_cal_num("≈150千卡"), 150)
        self.assertEqual(_cal_num("75 kcal/100g"), 75)

    def test_unknown_returns_zero(self):
        self.assertEqual(_cal_num("未知"), 0)


class RecommendViewTests(TestCase):
    """Limited unit tests for the Django view.

    Full functional coverage would require database fixtures which are outside
    the scope of this lightweight unit test file.
    """

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
