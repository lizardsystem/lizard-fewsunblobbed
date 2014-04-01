import logging

from django.shortcuts import get_object_or_404
from lizard_map.views import AppView

from lizard_fewsunblobbed.models import Filter


FILTER_CACHE_KEY = 'lizard.fewsunblobbed.views.filter_cache_key'
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
    # Originally something was cached here. That didn't play well with
    # lizard-security. Performance is good enough without filter caching,
    # so we just dump it without caching.
    return Filter.dump_bulk()


class FewsBrowserView(AppView):
    """Class based view for fews-unblobbed. TODO: Crumbs."""

    template_name = 'lizard_fewsunblobbed/fews_browser.html'
    edit_link = '/admin/lizard_fewsunblobbed/'

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
            return filter.used_parameters()
