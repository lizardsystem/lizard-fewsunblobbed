from django.shortcuts import render_to_response
from django.template import RequestContext

from lizard_fewsunblobbed.models import Filter
from lizard_fewsunblobbed.models import Timeserie
from lizard_map.models import WorkspaceManager


def fews_filter_tree(request, template='lizard_fewsunblobbed/filter_tree.html'):
    tree = Filter.dump_bulk()
    return render_to_response(template,
                              {"tree": tree},
                              context_instance=RequestContext(request))


def fews_parameter_tree(request, filterkey=90, locationkey=37551, template='lizard_fewsunblobbed/parameter_tree.html'):
    filtered_timeseries = Timeserie.objects.filter(filterkey=filterkey)
    parameters = [ts.parameterkey for ts in filtered_timeseries]
    p_list = list(set(parameters))
    filter = Filter.objects.get(pk=filterkey)
    return render_to_response(template,
                             {"parameters": p_list,
                              "filter": filter},
                              context_instance=RequestContext(request))


def fews_browser(request,
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

    return render_to_response(template,
                              {'filters': filters,
                               'found_filter': found_filter,
                               'parameters': parameters,
                               'workspaces': workspaces},
                              context_instance=RequestContext(request))
