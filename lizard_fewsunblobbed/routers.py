class FewsUnblobbedRouter(object):
    """Route all lizard_fewsunblobbed models to the 'fews-unblobbed' db."""

    def db_for_read(self, model, **hints):
        """Tell django to read our models from 'our' database"""
        if model._meta.app_label == 'lizard_fewsunblobbed':
            return 'fews-unblobbed'
        return None

    def db_for_write(self, model, **hints):
        """Tell django to read our models from 'our' database"""
        if model._meta.app_label == 'lizard_fewsunblobbed':
            # The database is read-only, but for testing we need to create
            # one.
            return 'fews-unblobbed'
        return None

    def allow_syncdb(self, db, model):
        """Allow only our models to be synced to our database.

        This actually means two things:

        - Our models should only end up in *our* dabase.

        - Only *our* models should end up in our database.

        The fews unblobbed database is read-only, but for testing we need to
        create one, therefore we need to allow syncdb.

        """
        if model._meta.app_label == 'contenttypes':
            # Temp hack, fixes http://code.djangoproject.com/ticket/12999
            # until django 1.2 beta 2 comes out.
            if db == 'fews-unblobbed':
                return True
        if model._meta.app_label == 'lizard_fewsunblobbed':
            if db == 'fews-unblobbed':
                return True
            return False
        if db == 'fews-unblobbed':
            return False
        return None  # None means 'no opinion'.
