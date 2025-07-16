from django.contrib import admin

from .models import Ingredient, Recipe, RecipeDetail, RecipeIngredient, ProteinRequirement, EnergyRequirement

admin.site.register(Ingredient)
admin.site.register(Recipe)
admin.site.register(RecipeDetail)
admin.site.register(RecipeIngredient)
admin.site.register(ProteinRequirement)
admin.site.register(EnergyRequirement)
