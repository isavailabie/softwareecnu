"""Database router to send all queries of the `recommender` app to the
`recommend` database.

Add `DATABASE_ROUTERS = ['mine.db_router.RecommendRouter']` in settings.py.
"""

class RecommendRouter:
    """A router to control all database operations for the recommender app."""

    app_label = 'recommender'

    def db_for_read(self, model, **hints):
        """Point read operations for recommender models to `recommend`."""
        if model._meta.app_label == self.app_label:
            return 'recommend'
        return None

    def db_for_write(self, model, **hints):
        """Point write operations for recommender models to `recommend`."""
        if model._meta.app_label == self.app_label:
            return 'recommend'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations if at least one model belongs to recommender."""
        if (
            obj1._meta.app_label == self.app_label or
            obj2._meta.app_label == self.app_label
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Ensure recommender app only appears in the `recommend` DB."""
        if app_label == self.app_label:
            return db == 'recommend'
        # Other apps should not migrate into recommend
        return db == 'default'
