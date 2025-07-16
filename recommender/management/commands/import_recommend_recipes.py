"""Import recipes specifically for `recommender` app to avoid command name clash
with the `fruit` app's `import_recipes`.

Usage:
    python manage.py import_recommend_recipes [json_path]
If `json_path` is omitted, falls back to the default hard-coded path.
"""

from .import_recipes import Command as _BaseCommand  # reuse logic

class Command(_BaseCommand):
    help = _BaseCommand.help + " (recommender version)"
