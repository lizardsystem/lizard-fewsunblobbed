import logging

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import get_object_or_404

from lizard_fewsunblobbed.models import Filter

from lizard_map.views import AppView

FILTER_CACHE_KEY = 'lizard_fewsunblobbed.views.filter_cache_key'
logger = logging.getLogger(__name__)


def filter_exclude(filters, exclude_filters):
    """ Filter out fews filters recursively. """
    for f in filters:
        if 'children' in f:
            f['children'] = filter_exclude(f['children'], exclude_filters)

    # Do not get confused, filter is a build-in function.
    return filter(
        lambda f: f['data']['fews_id'] not in exclude_filters, filters)


def fews_filters(ignore_cache=True):
    """
    Return fews filter tree.

    Exclude filters from settings.FEWS_UNBLOBBED_EXCLUDE_FILTERS.
    """
    filters = cache.get(FILTER_CACHE_KEY)
    # Filters is a list of dicts (keys: 'data', 'id', 'children')
    # In data, there's a key 'fews_id'
    if filters is None or ignore_cache:
        filters = Filter.dump_bulk()  # Optional: parent
        from pprint import pprint
        pprint(filters)

        # Filter out some root filters: get settings.
        try:
            exclude_filters = settings.FEWS_UNBLOBBED_EXCLUDE_FILTERS
            logger.info('Excluding filters: %r.' % exclude_filters)
        except AttributeError:
            exclude_filters = ['ZZL_Meteo', 'ZZL_ZUIV_RUW', ]
            logger.warning(
                'No setting FEWS_UNBLOBBED_EXCLUDE_FILTERS.'
                'By default ZZL_Meteo and ZZL_ZUIV_RUW are excluded.')
        # ^^^ Who on earth added these hardcoded items in the basic app?
        # a) settings.get(..., some_default) works fine.
        # b) Hardcoded settings for zzl? Just add them in the settings.py,
        #    then, if you're reading from it anyway!

        # Filter the filters.
        filters = filter_exclude(filters, exclude_filters)

        cache.set(FILTER_CACHE_KEY, filters, 8 * 60 * 60)  # 8 hours
    return filters


class FewsBrowserView(AppView):
    """Class based view for fews-unblobbed. TODO: Crumbs."""

    template_name = 'lizard_fewsunblobbed/fews_browser.html'

    def get(self, request, *args, **kwargs):
        """Overriden to get self.filterkey from the GET parameters.
           TODO: Do this in a nicer way."""

        try:
            self.filterkey = int(request.GET.get('filterkey', None))
        except (TypeError, ValueError):
            self.filterkey = None

        return super(FewsBrowserView, self).get(request, *args, **kwargs)

    def filters(self):
        if self.filterkey:
            return []
        else:
            return fews_filters()

    def found_filter(self):
        if self.filterkey:
            return get_object_or_404(Filter, pk=self.filterkey)
        else:
            return None

    def parameters(self):
        filter = self.found_filter()
        if filter:
            return filter.parameters()
