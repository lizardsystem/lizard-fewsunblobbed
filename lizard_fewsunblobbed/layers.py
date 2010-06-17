import os
import datetime
from math import sqrt

import mapnik
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.dates import date2num
from matplotlib.figure import Figure

from lizard_fewsunblobbed.models import Filter
from lizard_fewsunblobbed.models import Location
from lizard_fewsunblobbed.models import Timeserie
from lizard_map import coordinates
from lizard_map import workspace
from lizard_map.daterange import current_start_end_dates
from lizard_map.models import ICON_ORIGINALS
from lizard_map.symbol_manager import SymbolManager
from lizard_map.views import _inches_from_pixels
from lizard_map.views import SCREEN_DPI

# maps filter ids to icons
# TODO: remove from this file to a generic place
LAYER_STYLES = {
    "default": {'icon': 'meetpuntPeil.png',
                'mask': ('meetpuntPeil_mask.png', ),
                'color': (1, 1, 1, 0)},
    "boezem_waterstanden": {'icon': 'meetpuntPeil.png',
                            'mask': ('meetpuntPeil_mask.png', ),
                            'color': (0, 0.5, 1, 0)},
    "boezem_meetpunt": {'icon': 'meetpuntPeil.png',
                        'mask': ('meetpuntPeil_mask.png', ),
                        'color': (0, 1, 0, 0)},
    "boezem_poldergemaal": {'icon': 'gemaal.png',
                            'mask': ('gemaal_mask.png', ),
                            'color': (0, 1, 0, 0)},
    "west_opvoergemaal": {'icon': 'gemaal.png',
                          'mask': ('gemaal_mask.png', ),
                          'color': (1, 0, 1, 0)},
    "west_stuw_(hand)": {'icon': 'stuw.png',
                         'mask': ('stuw_mask.png', ),
                         'color': (0, 1, 0, 0)},
    "west_stuw_(auto)": {'icon': 'stuw.png',
                         'mask': ('stuw_mask.png', ),
                         'color': (1, 0, 0, 0)},
    "oost_stuw_(hand)": {'icon': 'stuw.png',
                         'mask': ('stuw_mask.png', ),
                         'color': (0, 1, 0, 0)},
    "oost_stuw_(auto)": {'icon': 'stuw.png',
                         'mask': ('stuw_mask.png', ),
                         'color': (1, 0, 0, 0)},
    "west_hevel": {'icon': 'hevel.png',
                   'mask': ('hevel_mask.png', ),
                   'color': (1, 1, 0, 0)},
    "waterketen_rioolgemalen": {'icon': 'gemaal.png',
                                'mask': ('gemaal_mask.png', ),
                                'color': (0.7, 0.5, 0, 0)},
    "waterketen_overstorten": {'icon': 'overstort.png',
                               'mask': ('overstort_mask.png', ),
                               'color': (1, 1, 1, 0)},
    }


def fews_symbol_name(filterkey):
    """Find fews symbol name"""

    # determine icon layout by looking at filter.id
    filter = get_object_or_404(Filter, pk=filterkey)
    if str(filter.fews_id) in LAYER_STYLES:
        icon_style = LAYER_STYLES[str(filter.fews_id)]
    else:
        icon_style = LAYER_STYLES['default']

    # apply icon layout using symbol manager
    symbol_manager = SymbolManager(
        ICON_ORIGINALS,
        os.path.join(settings.MEDIA_ROOT, 'generated_icons'))
    output_filename = symbol_manager.get_symbol_transformed(
        icon_style['icon'], **icon_style)

    return output_filename


class WorkspaceItemAdapterFewsUnblobbed(workspace.WorkspaceItemAdapter):
    """
    Should be registered as adapter_fews
    """
    def __init__(self, *args, **kwargs):
        super(WorkspaceItemAdapterFewsUnblobbed, self).__init__(*args, **kwargs)
        self.filterkey = self.layer_arguments['filterkey']
        self.parameterkey = self.layer_arguments['parameterkey']

    def layer(self, webcolor=None):
        """Return layer and styles that render points.

        """
        layers = []
        styles = {}
        layer = mapnik.Layer("FEWS points layer", coordinates.RD)
        filterkey = self.layer_arguments['filterkey']
        parameterkey = self.layer_arguments['parameterkey']

        # TODO: ^^^ translation!
        layer.datasource = mapnik.PointDatasource()
        if filterkey is None and parameterkey is None:
            # Grab the first 1000 locations
            locations = Location.objects.all()[:1000]
        else:
            locations = [timeserie.locationkey for timeserie in
                         Timeserie.objects.filter(filterkey=filterkey,
                                                  parameterkey=parameterkey)]
        for location in locations:
            layer.datasource.add_point(
                location.x, location.y, 'Name', str(location.name))

        output_filename = fews_symbol_name(filterkey)
        output_filename_abs = os.path.join(
            settings.MEDIA_ROOT, 'generated_icons', output_filename)

        # use filename in mapnik pointsymbolizer
        point_looks = mapnik.PointSymbolizer(output_filename_abs, 'png', 32, 32)

        point_looks.allow_overlap = True
        layout_rule = mapnik.Rule()
        layout_rule.symbols.append(point_looks)
        point_style = mapnik.Style()
        point_style.rules.append(layout_rule)

        # generate "unique" point style name and append to layer
        style_name = "Point style %s::%s" % (filterkey, parameterkey)
        styles[style_name] = point_style
        layer.styles.append(style_name)
        layers = [layer]
        return layers, styles

    def search(self, google_x, google_y, radius=None):
        """Return list of dict {'distance': <float>, 'timeserie':
        <timeserie>} of closest fews point that matches x, y, radius.

        """
        x, y = coordinates.google_to_rd(google_x, google_y)
        distances = [{'distance':
                          sqrt((timeserie.locationkey.x - x) ** 2 +
                               (timeserie.locationkey.y - y) ** 2),
                      # 'object': timeserie,
                      'name': timeserie.name,
                      'shortname': timeserie.shortname,
                      'workspace_item': self.workspace_item,
                      'identifier': { 'locationkey': timeserie.locationkey.pk },
                      'coords': timeserie.locationkey.google_coords(),
                      }
                     for timeserie in
                     Timeserie.objects.filter(filterkey=self.filterkey,
                                              parameterkey=self.parameterkey)]

        #filter out correct distances
        result = []
        for found_result in distances:
            if found_result['distance'] <= radius:
                result.append(found_result)

        result.sort(key=lambda item: item['distance'])
        return result

    def location(self, locationkey=None):
        """Return fews point representation corresponding to filter_id, location_id and
        parameter_id in same format as search function

        """
        timeserie = get_object_or_404(
            Timeserie, 
            filterkey=self.filterkey, 
            locationkey=locationkey,
            parameterkey=self.parameterkey)
        return {
            'name': timeserie.name,
            'shortname': timeserie.shortname,
            # 'object': timeserie,
            'workspace_item': self.workspace_item,
            'identifier': { 'locationkey': timeserie.locationkey.pk },
            'coords': timeserie.locationkey.google_coords(),
            }

    def image(self, identifier_list, start_end_dates, width=380.0, height=280.0):
        """
        Visualizes (timeserie) ids in a graph

        identifier_list: [{'locationkey': ...}, ...]
        start_end_dates: 2-tuple dates

        Draw graph(s) from fews unblobbed timeserie. Ids are set in GET
        parameter id (multiple ids allowed), or as a url parameter
        """
        timeserie = [get_object_or_404(Timeserie, 
                                       locationkey=identifier['locationkey'],
                                       filterkey=self.filterkey,
                                       parameterkey=self.parameterkey) 
                     for identifier in identifier_list]

        color_list = ['blue', 'green', 'cyan', 'magenta', 'black']
    
        figure = Figure()
        # Figure size
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
        axes.set_xlim(date2num(start_end_dates))

        canvas = FigureCanvas(figure)
        response = HttpResponse(content_type='image/png')
        canvas.print_png(response)
        return response
