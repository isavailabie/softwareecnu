from django.core.management.base import BaseCommand
from recommender.models import EnergyRequirement


class Command(BaseCommand):
    """Load energy (calorie) recommendation data into the given database.
    Usage: python manage.py load_energy [--database recommend]
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            default="recommend",
            help="Database alias to write to (default: recommend)",
        )

    def handle(self, *args, **options):
        db_alias = options["database"]
        records = get_records()
        field_names = ["sex", "pal_level", "age_min", "age_max", "value", "unit"]
        objs = [EnergyRequirement(**dict(zip(field_names, rec))) for rec in records]
        EnergyRequirement.objects.using(db_alias).bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f"Inserted/kept {len(objs)} energy requirement rows into '{db_alias}' database."))


def get_records():
    """Return list of tuples for energy requirement."""
    d = []
    # Male PAL I
    d += [
        ("M", "I", 1, 1, "900", "kcal/d"),
        ("M", "I", 2, 2, "1100", "kcal/d"),
        ("M", "I", 3, 3, "1250", "kcal/d"),
        ("M", "I", 4, 4, "1300", "kcal/d"),
        ("M", "I", 5, 5, "1400", "kcal/d"),
        ("M", "I", 6, 6, "1400", "kcal/d"),
        ("M", "I", 7, 7, "1500", "kcal/d"),
        ("M", "I", 8, 8, "1600", "kcal/d"),
        ("M", "I", 9, 9, "1700", "kcal/d"),
        ("M", "I", 10, 10, "1800", "kcal/d"),
        ("M", "I", 11, 11, "1900", "kcal/d"),
        ("M", "I", 12, 14, "2300", "kcal/d"),
        ("M", "I", 15, 17, "2600", "kcal/d"),
        ("M", "I", 18, 29, "2150", "kcal/d"),
        ("M", "I", 30, 49, "2050", "kcal/d"),
        ("M", "I", 50, 64, "1950", "kcal/d"),
        ("M", "I", 65, 74, "1900", "kcal/d"),
        ("M", "I", 75, 120, "1800", "kcal/d"),
    ]
    # Male PAL II (only starting from 0 age kcal/kg then 6y)
    d += [
        ("M", "II", 0, 0, "90", "kcal/(kg·d)"),
        ("M", "II", 0, 1, "75", "kcal/(kg·d)"),
        ("M", "II", 6, 6, "1600", "kcal/d"),
        ("M", "II", 7, 7, "1700", "kcal/d"),
        ("M", "II", 8, 8, "1600", "kcal/d"),
        ("M", "II", 9, 9, "1700", "kcal/d"),
        ("M", "II", 10, 10, "2050", "kcal/d"),
        ("M", "II", 11, 11, "2300", "kcal/d"),
        ("M", "II", 12, 14, "2600", "kcal/d"),
        ("M", "II", 15, 17, "2950", "kcal/d"),
        ("M", "II", 18, 29, "2550", "kcal/d"),
        ("M", "II", 30, 49, "2500", "kcal/d"),
        ("M", "II", 50, 64, "2400", "kcal/d"),
        ("M", "II", 65, 74, "2300", "kcal/d"),
        ("M", "II", 75, 120, "2200", "kcal/d"),
    ]
    # Male PAL III
    d += [
        ("M", "III", 6, 6, "1800", "kcal/d"),
        ("M", "III", 7, 7, "1900", "kcal/d"),
        ("M", "III", 8, 8, "2100", "kcal/d"),
        ("M", "III", 9, 9, "2200", "kcal/d"),
        ("M", "III", 10, 10, "2300", "kcal/d"),
        ("M", "III", 11, 11, "2450", "kcal/d"),
        ("M", "III", 12, 14, "2900", "kcal/d"),
        ("M", "III", 15, 17, "3300", "kcal/d"),
        ("M", "III", 18, 29, "3000", "kcal/d"),
        ("M", "III", 30, 49, "2950", "kcal/d"),
        ("M", "III", 50, 64, "2800", "kcal/d"),
    ]
    # Female PAL I
    d += [
        ("F", "I", 1, 1, "800", "kcal/d"),
        ("F", "I", 2, 2, "1000", "kcal/d"),
        ("F", "I", 3, 3, "1150", "kcal/d"),
        ("F", "I", 4, 4, "1250", "kcal/d"),
        ("F", "I", 5, 5, "1300", "kcal/d"),
        ("F", "I", 6, 6, "1300", "kcal/d"),
        ("F", "I", 7, 7, "1350", "kcal/d"),
        ("F", "I", 8, 8, "1450", "kcal/d"),
        ("F", "I", 9, 9, "1550", "kcal/d"),
        ("F", "I", 10, 10, "1550", "kcal/d"),
        ("F", "I", 11, 11, "1650", "kcal/d"),
        ("F", "I", 12, 14, "1750", "kcal/d"),
        ("F", "I", 15, 17, "1850", "kcal/d"),
        ("F", "I", 18, 29, "1700", "kcal/d"),
        ("F", "I", 30, 49, "1650", "kcal/d"),
        ("F", "I", 50, 64, "1600", "kcal/d"),
        ("F", "I", 65, 74, "1550", "kcal/d"),
        ("F", "I", 75, 120, "1500", "kcal/d"),
    ]
    # Female PAL II
    d += [
        ("F", "II", 0, 0, "90", "kcal/(kg·d)"),
        ("F", "II", 0, 1, "75", "kcal/(kg·d)"),
        ("F", "II", 6, 6, "1450", "kcal/d"),
        ("F", "II", 7, 7, "1550", "kcal/d"),
        ("F", "II", 8, 8, "1550", "kcal/d"),
        ("F", "II", 9, 9, "1700", "kcal/d"),
        ("F", "II", 10, 10, "1800", "kcal/d"),
        ("F", "II", 11, 11, "2000", "kcal/d"),
        ("F", "II", 12, 14, "2250", "kcal/d"),
        ("F", "II", 15, 17, "2400", "kcal/d"),
        ("F", "II", 18, 29, "2100", "kcal/d"),
        ("F", "II", 30, 49, "2050", "kcal/d"),
        ("F", "II", 50, 64, "2000", "kcal/d"),
        ("F", "II", 65, 74, "1950", "kcal/d"),
        ("F", "II", 75, 120, "1900", "kcal/d"),
    ]
    # Female PAL III
    d += [
        ("F", "III", 6, 6, "1650", "kcal/d"),
        ("F", "III", 7, 7, "1750", "kcal/d"),
        ("F", "III", 8, 8, "1900", "kcal/d"),
        ("F", "III", 9, 9, "2000", "kcal/d"),
        ("F", "III", 10, 10, "2100", "kcal/d"),
        ("F", "III", 11, 11, "2250", "kcal/d"),
        ("F", "III", 12, 14, "2450", "kcal/d"),
        ("F", "III", 15, 17, "2650", "kcal/d"),
        ("F", "III", 18, 29, "2450", "kcal/d"),
        ("F", "III", 30, 49, "2400", "kcal/d"),
        ("F", "III", 50, 64, "2300", "kcal/d"),
    ]
    return d
