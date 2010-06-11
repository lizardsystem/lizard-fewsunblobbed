import datetime
import simplejson

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.dates import date2num
from matplotlib.figure import Figure

from lizard_fewsunblobbed.models import Filter
from lizard_fewsunblobbed.models import Timeserie
from lizard_map import coordinates
from lizard_map.daterange import current_start_end_dates
from lizard_map.views import _inches_from_pixels
from lizard_map.views import popup_json
from lizard_map.views import SCREEN_DPI
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


def timeserie_graph(request, id=None):
    """
    Draw graph(s) from fews unblobbed timeserie. Ids are set in GET
    parameter id (multiple ids allowed), or as a url parameter
    """
    color_list = ['blue', 'green', 'cyan', 'magenta', 'black']

    if id is None:
        # get timeserie id's from GET parameter
        timeserie_ids = request.GET.getlist('id')
        timeserie = [get_object_or_404(Timeserie, pk=id) for id in timeserie_ids]
    else:
        # get timeserie id from url parameter
        timeserie = [get_object_or_404(Timeserie, pk=id), ]
    figure = Figure()
    # Figure size
    width = request.GET.get('width', 380)
    height = request.GET.get('height', 280)
    width = float(width)
    height = float(height)
    figure.set_size_inches((_inches_from_pixels(width),
                            _inches_from_pixels(height)))
    figure.set_dpi(SCREEN_DPI)
    # Figure color
    figure.set_facecolor('white')

    axes = figure.add_subplot(111)
    # Title.
    if len(timeserie) <= 1:
        figure.suptitle('/'.join([single_timeserie.name for single_timeserie in timeserie]))
    else:
        figure.suptitle('multiple graphs')
    axes.grid(True)
    today = datetime.datetime.now()
    #start_date = today - datetime.timedelta(days=450)
    
    for index, single_timeserie in enumerate(timeserie):
        dates = []
        values = []
        for data in single_timeserie.timeseriedata.all():
            dates.append(data.tsd_time)
            values.append(data.tsd_value)
        axes.plot(dates, values,
                  lw=1,
                  color=color_list[index % len(color_list)])
    # Show line for today.
    axes.axvline(today, color='blue', lw=1, ls='--')
    # axvspan for years/seasons.

    # Date range
    axes.set_xlim(date2num(current_start_end_dates(request)))

    canvas = FigureCanvas(figure)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response


def search_fews_points(request):
    """searches for fews point nearest to GET x,y, returns json_popup
    of results"""
    workspace_manager = WorkspaceManager(request)
    workspace_collections = workspace_manager.load_or_create()

    # xy params from the GET request.
    google_x = float(request.GET.get('x'))
    google_y = float(request.GET.get('y'))
    x, y = coordinates.google_to_rd(google_x, google_y)

    found = []
    for workspace_collection in workspace_collections.values():
        for workspace in workspace_collection:
            for workspace_item in workspace.workspace_items.filter(visible=True):
                search_results = workspace_item.adapter.search(x, y)
                found += search_results

    if found:
        return popup_json(found)
    else:
        result = {'id': 'popup_nothing_found',
                  'objects': [{'html': 'Niets gevonden.',
                               'x': google_x,
                               'y': google_y }]
                  }
        return HttpResponse(simplejson.dumps(result))
