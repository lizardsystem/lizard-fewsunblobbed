def is_fews_model(model):
    return hasattr(model._meta, 'is_fews_model') and model._meta.is_fews_model

class FewsUnblobbedRouter(object):
    """Route all lizard_fewsunblobbed models to the 'fewsnorm' db."""

    def db_for_read(self, model, **hints):
        """Tell django to read our models from 'our' database"""
        if is_fews_model(model):
            return 'fewsnorm'
        return None

    def db_for_write(self, model, **hints):
        """Tell django to read our models from 'our' database"""
        if is_fews_model(model):
            # The database is read-only, but for testing we need to create one.
            return 'fewsnorm'
        return None

    def allow_syncdb(self, db, model):
        """Allow only our models to be synced to our database.

        This actually means two things:

        - Our models should only end up in *our* dabase.

        - Only *our* models should end up in our database.

        The fews unblobbed database is read-only, but for testing we need to
        create one, therefore we need to allow syncdb.

        """
        #if model._meta.app_label in ('sites', 'south'):
        #    # Hack for bug https://code.djangoproject.com/ticket/16353
        #    # When testing, create django_site and south in both databases
        #    if db == 'fews-norm-ora':
        #        return True

        # only decide for this app
        if model._meta.app_label == 'lizard_fewsunblobbed':
            # only allow fews models to sync to the fewsnorm db
            if is_fews_model(model):
                return db == 'fewsnorm'
            # explicitly disallow other models to sync to the fewsnorm db
            if db == 'fewsnorm':
                return False
        else:
            # explicitly disallow any other apps their models to sync to the fewsnorm db
            if db == 'fewsnorm':
                return False
        # no opinion on all other combinations
        return None  # None means 'no opinion'.
