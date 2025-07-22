"""Integration tests for `recommend_view` covering main logic paths."""

import json
from datetime import datetime
from unittest.mock import patch

from django.test import TestCase, RequestFactory
from django.utils import timezone
from django.utils.timezone import get_current_timezone

from .models import RecipeFlat
from .views import recommend_view


class RecommendViewIntegrationTests(TestCase):
    # Enable the additional database alias used by the recommender router.
    databases = {"default", "recommend"}
    """End-to-end tests for `recommend_view`."""

    def setUp(self):
        self.factory = RequestFactory()
        # Create complete recipe fixtures with all required fields
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
        """Helper method to create POST request."""
        return self.factory.post(
            "/recommender/recommend/",
            data=json.dumps(body_dict),
            content_type="application/json",
        )

    @patch.dict("os.environ", {"CHATECNU_API_KEY": "test_key"})
    @patch("recommender.views.RecipeFlat.objects.using")
    @patch("recommender.views.timezone.localtime")
    def test_recommend_view_basic(self, mock_localtime, mock_using, *args):
        """Test that the view returns a successful response."""
        # 1. Mock the current time (8:00 AM)
        mock_localtime.return_value = timezone.make_aware(
            datetime(2025, 7, 22, 8, 0, 0),
            timezone=get_current_timezone()
        )
        
        # 2. Mock the database query to use test database
        mock_using.return_value = RecipeFlat.objects
        
        # 3. Prepare test payload
        payload = {
            "available_ingredients": ["番茄", "鸡蛋"],
            "physical_data": [{
                "age": 30,
                "sex": "M",
                "activity_level": "moderate"
            }],
            "history": [],
        }
        
        # 4. Make the request
        request = self._post(payload)
        response = recommend_view(request)
        
        # 5. Verify successful response
        self.assertEqual(response.status_code, 200)