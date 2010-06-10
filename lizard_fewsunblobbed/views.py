from django.shortcuts import render_to_response
from django.template import RequestContext

from lizard_fewsunblobbed.models import Filter
from lizard_fewsunblobbed.models import Timeserie
from lizard_map.workspace import WorkspaceManager


def fews_browser(request,
                 javascript_click_handler=None,
                 template="lizard_fewsunblobbed/fews_browser.html"):
    workspace_manager = WorkspaceManager(request)
    workspaces = workspace_manager.load_or_create()
    filters = Filter.dump_bulk()

    filterkey = request.GET.get('filterkey', None)
    if filterkey is None:
        found_filter = None
        parameters = None
    else:
        filterkey = int(filterkey)
        found_filter = Filter.objects.get(pk=filterkey)
        filtered_timeseries = Timeserie.objects.filter(filterkey=filterkey)
        parameters = [ts.parameterkey for ts in filtered_timeseries]
        parameters = list(set(parameters))

    return render_to_response(
        template,
        {'filters': filters,
         'found_filter': found_filter,
         'parameters': parameters,
         'javascript_click_handler': javascript_click_handler,
         'workspaces': workspaces},
        context_instance=RequestContext(request))
