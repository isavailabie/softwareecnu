"""Import recipes from a JSON file into the recommender database.

Usage:
    python manage.py import_recipes <path_to_json>

The JSON should be either:
1. A list of recipe objects, or
2. A single recipe object.

Each object expected keys (missing keys are allowed):
    dish_name (str)         – 菜名 -> Recipe.title
    image_url (str)
    image_path (str)
    calories (str)
    nutrition (dict)
    description (str)
    cook_time (str)
    difficulty (str)
    servings (str)
    category (str)
    steps (list[str])
    ingredients (list[{name, amount}])

The command is idempotent: it uses get_or_create to avoid duplicates.
The recommender app is routed to the `recommend` database via DATABASE_ROUTERS,
so all writes land in recommend.sqlite3 automatically.
"""

import json
from pathlib import Path
from recommender.models import RecipeFlat 
from django.core.management.base import BaseCommand, CommandError

from recommender.models import (
    Ingredient,
    Recipe,
    RecipeDetail,
    RecipeIngredient,
)


class Command(BaseCommand):
    help = "Import recipes from a JSON file into recommender database"

    def add_arguments(self, parser):
        # Use positional arg 'json_path' (string). Still keep for help display.
        parser.add_argument("json_path", nargs="?", type=str, help="Absolute path to json file (optional)")
        parser.add_argument("--category", type=str, help="Default category tag for all imported recipes if JSON lacks it")

    def handle(self, *args, **options):
        json_path_str = None
        if args:
            json_path_str = args[0]
        else:
            json_path_opt = options.get("json_path")   
            if isinstance(json_path_opt, list):
                json_path_opt = json_path_opt[0] if json_path_opt else None
            json_path_str = json_path_opt

        default_category = options.get("category")
        # Default path fallback
        
        if not json_path_str:
            json_path_str = r"F:\programming\data\liangcai1.json"

        json_path = Path(json_path_str).expanduser()
        if not json_path.exists():
            raise CommandError(f"File not found: {json_path}")

        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CommandError(f"JSON decode error: {exc}") from exc

        # Ensure we have iterable list
        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            raise CommandError("JSON root must be object or array")

        created, updated = 0, 0
        for item in data:
            title = item.get("dish_name") or item.get("title")
            if not title:
                self.stderr.write(self.style.WARNING("Skip item without dish_name"))
                continue

            recipe, r_created = Recipe.objects.get_or_create(title=title)
            if r_created:
                created += 1
            else:
                updated += 1

            # Update or create detail
            detail_defaults = {
                "image_url": item.get("image_url", ""),
                "image_path": item.get("image_path", ""),
                "calories": item.get("calories", ""),
                "nutrition": item.get("nutrition", {}),
                "description": item.get("description", ""),
                "cook_time": item.get("cook_time", ""),
                "difficulty": item.get("difficulty", ""),
                "servings": item.get("servings", ""),
                "steps": item.get("steps", []),
                "category": item.get("category", default_category or "unknown"),
            }
            RecipeDetail.objects.update_or_create(recipe=recipe, defaults=detail_defaults)

            # Upsert flat table
            flat_defaults = detail_defaults | {
                "category": detail_defaults["category"],
                "ingredients": item.get("ingredients", []),
            }
            RecipeFlat.objects.update_or_create(title=title, defaults=flat_defaults)

            # Process ingredients
            for ing in item.get("ingredients", []):
                name = ing.get("name") or ing.get("ingredient")
                if not name:
                    continue
                ing_obj, _ = Ingredient.objects.get_or_create(name=name)
                RecipeIngredient.objects.get_or_create(
                    recipe=recipe,
                    ingredient=ing_obj,
                    defaults={"amount": ing.get("amount", "")},
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Import completed. New: {created}, Existing updated/kept: {updated}"
            )
        )
