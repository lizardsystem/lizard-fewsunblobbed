import logging

from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext

from lizard_fewsunblobbed.models import Filter
from lizard_fewsunblobbed.models import Parameter

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


def fews_browser(request,
                 template="lizard_fewsunblobbed/fews_browser.html",
                 crumbs_prepend=None):
    filterkey = request.GET.get('filterkey', None)

    if filterkey is None:
        filters = fews_filters()
        found_filter = None
        parameters = None
    else:
        filters = []  # We don't need to return them in the template.
        filterkey = int(filterkey)
        found_filter = get_object_or_404(Filter, pk=filterkey)
        parameter_cache_key = FILTER_CACHE_KEY + str(filterkey)
        parameters = cache.get(parameter_cache_key)
        if 1:  #parameters is None:
            parameters = []  # Start new one
            # Fetch all filter -> parameter combinations.
            for f in [found_filter] + found_filter.get_descendants():
                for p in Parameter.objects.filter(
                    timeserie__filterkey=f).distinct():

                    # Add filterkey for use in template (it's a m2m).
                    p.filterkey = f
                    if f <> found_filter:
                        p.name = '%s (%s)' % (p.name, f.name)
                    parameters.append(p)

            # parameters = param_dict.values()
            parameters.sort(key=lambda p: p.name)
            cache.set(parameter_cache_key, parameters, 8 * 60 * 60)

    if crumbs_prepend is not None:
        crumbs = list(crumbs_prepend)
    else:
        crumbs = [{'name': 'home', 'url': '/'}]
    crumbs.append({'name': 'metingen',
                   'url': reverse('fews_browser')})

    return render_to_response(
        template,
        {'filters': filters,
         'found_filter': found_filter,
         'parameters': parameters,
         'crumbs': crumbs},
        context_instance=RequestContext(request))
