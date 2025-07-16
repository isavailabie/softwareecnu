from django.urls import path

from .views import recommend_view

app_name = "recommender"

urlpatterns = [
    path("recommend/", recommend_view, name="recommend"),
]
