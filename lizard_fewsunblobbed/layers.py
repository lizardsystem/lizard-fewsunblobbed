import os
import datetime
from math import sqrt

import mapnik
from django.conf import settings
from django.shortcuts import get_object_or_404

from lizard_fewsunblobbed.models import Filter
from lizard_fewsunblobbed.models import Location
from lizard_fewsunblobbed.models import Timeserie
from lizard_map import coordinates
from lizard_map import workspace
from lizard_map.adapter import Graph
from lizard_map.models import ICON_ORIGINALS
from lizard_map.symbol_manager import SymbolManager

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

    def layer(self, layer_ids=None, webcolor=None):
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
                      'identifier': {'locationkey': timeserie.locationkey.pk},
                      'google_coords': timeserie.locationkey.google_coords(),
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
        """Return fews point representation corresponding to
        filter_id, location_id and parameter_id in same format as
        search function

        """
        timeserie = get_object_or_404(
            Timeserie, 
            filterkey=self.filterkey, 
            locationkey=locationkey,
            parameterkey=self.parameterkey)
        return {
            'name': timeserie.name,
            'shortname': timeserie.shortname,
            'workspace_item': self.workspace_item,
            'identifier': {'locationkey': timeserie.locationkey.pk},
            'google_coords': timeserie.locationkey.google_coords(),
            }

    def image(self, 
              identifier_list, 
              start_date,
              end_date, 
              width=380.0, 
              height=250.0):
        """
        Visualizes (timeserie) ids in a graph

        identifier_list: [{'locationkey': ...}, ...]
        start_date, end_date: dates

        Draw graph(s) from fews unblobbed timeserie. Ids are set in GET
        parameter id (multiple ids allowed), or as a url parameter
        """
        timeserie = [get_object_or_404(Timeserie, 
                                       locationkey=identifier['locationkey'],
                                       filterkey=self.filterkey,
                                       parameterkey=self.parameterkey) 
                     for identifier in identifier_list]

        color_list = ['blue', 'green', 'cyan', 'magenta', 'black']
        today = datetime.datetime.now()

        graph = Graph(start_date, end_date, 
                      width=width, height=height, today=today)
        
        # Title.
        if len(timeserie) <= 1:
            title = '/'.join([single_timeserie.name 
                              for single_timeserie in timeserie])
        else:
            title = 'multiple graphs'
        graph.suptitle(title)
        graph.axes.grid(True)

        # Draw the actual graph lines
        for index, single_timeserie in enumerate(timeserie):
            dates = []
            values = []
            for data in single_timeserie.timeseriedata.all():
                dates.append(data.tsd_time)
                values.append(data.tsd_value)
            graph.axes.plot(dates, values,
                            lw=1,
                            color=color_list[index % len(color_list)])

        graph.add_today()
        return graph.http_png()
