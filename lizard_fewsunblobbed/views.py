import logging

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from lizard_map.views import AppView

from lizard_fewsunblobbed.models import Filter


FILTER_CACHE_KEY = 'lizard_fewsunblobbed.views.filter_cache_key2'
logger = logging.getLogger(__name__)


def filter_exclude(filters, exclude_filters):
    """ Filter out fews filters recursively. """
    for f in filters:
        if 'children' in f:
            f['children'] = filter_exclude(f['children'], exclude_filters)

    # Do not get confused, filter is a build-in function.
    return filter(
        lambda f: f['data']['fews_id'] not in exclude_filters, filters)


def fews_filters(ignore_cache=False):
    """
    Return fews filter tree.

    Exclude filters from settings.FEWS_UNBLOBBED_EXCLUDE_FILTERS.
    """
    filters = cache.get(FILTER_CACHE_KEY)
    # Filters is a list of dicts (keys: 'data', 'id', 'children')
    # In data, there's a key 'fews_id'
    if filters is None or ignore_cache:
        filters = Filter.dump_bulk()  # Optional: parent

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

    @cached_property
    def filterkey(self):
        key = self.request.GET.get('filterkey')
        if not key:
            return
        return int(key)

    def filters(self):
        if self.filterkey:
            return []
        else:
            return fews_filters()

    @cached_property
    def found_filter(self):
        if self.filterkey is not None:
            return get_object_or_404(Filter, pk=self.filterkey)

    def parameters(self):
        if self.filterkey is None:
            return
        return self.found_filter.parameters()
