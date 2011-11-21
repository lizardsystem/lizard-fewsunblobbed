class FewsUnblobbedRouter(object):
    """Route all lizard_fewsunblobbed models to the 'fews-unblobbed' db.
    Except for Icon Styles! We can't expect them to be present
    in the customer's FEWS database..."""

    def db_for_read(self, model, **hints):
        """Tell django to read our models from 'our' database"""
        if model._meta.app_label == 'lizard_fewsunblobbed':
            if model._meta.object_name == 'IconStyle':
                # Not this one
                return None
            return 'fews-unblobbed'
        return None

    def db_for_write(self, model, **hints):
        """Tell django to read our models from 'our' database"""
        if model._meta.app_label == 'lizard_fewsunblobbed':
            if model._meta.object_name == 'IconStyle':
                # Create this one in the normal database
                return None

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
        if model._meta.app_label in ('sites', 'south'):
            # Hack for bug https://code.djangoproject.com/ticket/16353
            # When testing, create django_site and south in both databases
            if db == 'fews-unblobbed':
                return True

        if model._meta.app_label == 'lizard_fewsunblobbed':
            if db == 'fews-unblobbed':
                if model._meta.object_name == 'IconStyle':
                    # Not this one
                    return False
                return True
            return False
        if db == 'fews-unblobbed':
            return False
        return None  # None means 'no opinion'.
