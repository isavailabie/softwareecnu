from django.core.management.base import BaseCommand
from recommender.models import ProteinRequirement


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            default="recommend",
            help="Database alias to write to (default: recommend)",
        )
    """Load protein requirement reference values into the database.

    Usage:
        python manage.py load_protein
    """

    def handle(self, *args, **options):
        db_alias = options["database"]
        records = get_records()
        field_names = ["sex", "req_type", "age_min", "age_max", "value", "unit"]
        objs = [ProteinRequirement(**dict(zip(field_names, rec))) for rec in records]
        ProteinRequirement.objects.using(db_alias).bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f"Inserted/kept {len(objs)} protein requirement rows into '{db_alias}' database."))


def get_records():
    """Return list of tuples representing protein requirement rows."""
    # Data taken from Chinese Dietary Reference Intakes (2023) – protein.
    data = [
        # male EAR (g/d)
        ("M", "EAR", 1, 1, "20", "g/d"),
        ("M", "EAR", 2, 2, "20", "g/d"),
        ("M", "EAR", 3, 3, "25", "g/d"),
        ("M", "EAR", 4, 4, "25", "g/d"),
        ("M", "EAR", 5, 5, "25", "g/d"),
        ("M", "EAR", 6, 6, "30", "g/d"),
        ("M", "EAR", 7, 7, "30", "g/d"),
        ("M", "EAR", 8, 8, "35", "g/d"),
        ("M", "EAR", 9, 9, "40", "g/d"),
        ("M", "EAR", 10, 10, "40", "g/d"),
        ("M", "EAR", 11, 11, "45", "g/d"),
        ("M", "EAR", 12, 14, "55", "g/d"),
        ("M", "EAR", 15, 17, "60", "g/d"),
        ("M", "EAR", 18, 49, "60", "g/d"),
        ("M", "EAR", 50, 64, "60", "g/d"),
        ("M", "EAR", 65, 74, "60", "g/d"),
        ("M", "EAR", 75, 120, "60", "g/d"),  # 75岁及以上
        # male RNI
        ("M", "RNI", 0, 0, "9", "g/d"),
        ("M", "RNI", 0, 1, "17", "g/d"),  # 0.5岁
        ("M", "RNI", 1, 1, "25", "g/d"),
        ("M", "RNI", 2, 2, "25", "g/d"),
        ("M", "RNI", 3, 3, "30", "g/d"),
        ("M", "RNI", 4, 4, "30", "g/d"),
        ("M", "RNI", 5, 5, "30", "g/d"),
        ("M", "RNI", 6, 6, "35", "g/d"),
        ("M", "RNI", 7, 7, "40", "g/d"),
        ("M", "RNI", 8, 8, "40", "g/d"),
        ("M", "RNI", 9, 9, "45", "g/d"),
        ("M", "RNI", 10, 10, "50", "g/d"),
        ("M", "RNI", 11, 11, "55", "g/d"),
        ("M", "RNI", 12, 14, "70", "g/d"),
        ("M", "RNI", 15, 17, "75", "g/d"),
        ("M", "RNI", 18, 29, "65", "g/d"),
        ("M", "RNI", 30, 49, "65", "g/d"),
        ("M", "RNI", 50, 64, "65", "g/d"),
        ("M", "RNI", 65, 74, "72", "g/d"),
        ("M", "RNI", 75, 120, "72", "g/d"),
        # male AMDR (%E)
        ("M", "AMDR", 4, 4, "8-20", "%E"),
        ("M", "AMDR", 5, 5, "8-20", "%E"),
        ("M", "AMDR", 6, 6, "10-20", "%E"),
        ("M", "AMDR", 7, 7, "10-20", "%E"),
        ("M", "AMDR", 8, 8, "10-20", "%E"),
        ("M", "AMDR", 9, 9, "10-20", "%E"),
        ("M", "AMDR", 10, 10, "10-20", "%E"),
        ("M", "AMDR", 11, 11, "10-20", "%E"),
        ("M", "AMDR", 12, 14, "10-20", "%E"),
        ("M", "AMDR", 15, 17, "10-20", "%E"),
        ("M", "AMDR", 18, 49, "10-20", "%E"),
        ("M", "AMDR", 50, 64, "10-20", "%E"),
        ("M", "AMDR", 65, 74, "15-20", "%E"),
        ("M", "AMDR", 75, 120, "15-20", "%E"),
        # female EAR
        ("F", "EAR", 1, 1, "20", "g/d"),
        ("F", "EAR", 2, 2, "20", "g/d"),
        ("F", "EAR", 3, 3, "25", "g/d"),
        ("F", "EAR", 4, 4, "25", "g/d"),
        ("F", "EAR", 5, 5, "25", "g/d"),
        ("F", "EAR", 6, 6, "30", "g/d"),
        ("F", "EAR", 7, 7, "30", "g/d"),
        ("F", "EAR", 8, 8, "35", "g/d"),
        ("F", "EAR", 9, 9, "40", "g/d"),
        ("F", "EAR", 10, 10, "40", "g/d"),
        ("F", "EAR", 11, 11, "45", "g/d"),
        ("F", "EAR", 12, 14, "50", "g/d"),
        ("F", "EAR", 15, 17, "50", "g/d"),
        ("F", "EAR", 18, 49, "50", "g/d"),
        ("F", "EAR", 50, 64, "50", "g/d"),
        ("F", "EAR", 65, 74, "50", "g/d"),
        ("F", "EAR", 75, 120, "50", "g/d"),
        # female RNI
        ("F", "RNI", 0, 0, "9", "g/d"),
        ("F", "RNI", 0, 1, "17", "g/d"),
        ("F", "RNI", 1, 1, "25", "g/d"),
        ("F", "RNI", 2, 2, "25", "g/d"),
        ("F", "RNI", 3, 3, "30", "g/d"),
        ("F", "RNI", 4, 4, "30", "g/d"),
        ("F", "RNI", 5, 5, "30", "g/d"),
        ("F", "RNI", 6, 6, "35", "g/d"),
        ("F", "RNI", 7, 7, "40", "g/d"),
        ("F", "RNI", 8, 8, "40", "g/d"),
        ("F", "RNI", 9, 9, "45", "g/d"),
        ("F", "RNI", 10, 10, "50", "g/d"),
        ("F", "RNI", 11, 11, "55", "g/d"),
        ("F", "RNI", 12, 14, "60", "g/d"),
        ("F", "RNI", 15, 17, "60", "g/d"),
        ("F", "RNI", 18, 29, "55", "g/d"),
        ("F", "RNI", 30, 49, "55", "g/d"),
        ("F", "RNI", 50, 64, "55", "g/d"),
        ("F", "RNI", 65, 74, "62", "g/d"),
        ("F", "RNI", 75, 120, "62", "g/d"),
        # female AMDR
        ("F", "AMDR", 4, 4, "8-20", "%E"),
        ("F", "AMDR", 5, 5, "8-20", "%E"),
        ("F", "AMDR", 6, 6, "10-20", "%E"),
        ("F", "AMDR", 7, 7, "10-20", "%E"),
        ("F", "AMDR", 8, 8, "10-20", "%E"),
        ("F", "AMDR", 9, 9, "10-20", "%E"),
        ("F", "AMDR", 10, 10, "10-20", "%E"),
        ("F", "AMDR", 11, 11, "10-20", "%E"),
        ("F", "AMDR", 12, 14, "10-20", "%E"),
        ("F", "AMDR", 15, 17, "10-20", "%E"),
        ("F", "AMDR", 18, 49, "10-20", "%E"),
        ("F", "AMDR", 50, 64, "10-20", "%E"),
        ("F", "AMDR", 65, 74, "15-20", "%E"),
        ("F", "AMDR", 75, 120, "15-20", "%E")
    ]
    return data
