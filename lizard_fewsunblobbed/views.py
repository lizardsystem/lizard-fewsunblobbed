import simplejson

from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

from lizard_fewsunblobbed.models import Filter
from lizard_fewsunblobbed.models import Parameter
from lizard_map import coordinates
from lizard_map.daterange import current_start_end_dates
from lizard_map.daterange import DateRangeForm
from lizard_map.views import popup_json
from lizard_map.workspace import WorkspaceManager

FILTER_CACHE_KEY = 'lizard.fewsunblobbed.views.filter_cache_key'


def fews_browser(request,
                 javascript_click_handler=None,
                 template="lizard_fewsunblobbed/fews_browser.html"):
    workspace_manager = WorkspaceManager(request)
    workspaces = workspace_manager.load_or_create()
    date_range_form = DateRangeForm(
        current_start_end_dates(request, for_form=True))
    filters = cache.get(FILTER_CACHE_KEY)
    if filters is None:
        filters = Filter.dump_bulk()
        cache.set(FILTER_CACHE_KEY, filters, 8 * 60 * 60)

    filterkey = request.GET.get('filterkey', None)
    if filterkey is None:
        found_filter = None
        parameters = None
    else:
        filterkey = int(filterkey)
        found_filter = Filter.objects.get(pk=filterkey)
        parameter_cache_key = FILTER_CACHE_KEY + str(filterkey)
        parameters = cache.get(parameter_cache_key)
        if parameters is None:
            parameters = Parameter.objects.filter(
                timeserie__filterkey=filterkey).distinct()
            cache.set(parameter_cache_key, parameters, 8 * 60 * 60)

    return render_to_response(
        template,
        {'filters': filters,
         'found_filter': found_filter,
         'parameters': parameters,
         'date_range_form': date_range_form,
         'javascript_click_handler': javascript_click_handler,
         'workspaces': workspaces},
        context_instance=RequestContext(request))


def timeserie(request, filterkey, locationkey, parameterkey):
    return HttpResponse("not implemented yet")
