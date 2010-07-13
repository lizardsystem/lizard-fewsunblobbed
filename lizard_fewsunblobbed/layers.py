import os
import datetime
import copy
from math import sqrt

import mapnik
from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
import simplejson as json

from lizard_fewsunblobbed.models import Filter
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
                'color': (0, 0, 1, 0)},
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
    "Watkwal_Zwemwater_ALG": {'icon': 'meetpuntPeil.png',
                              'mask': ('meetpuntPeil_mask.png', ),
                              'color': (0, 1.0, 0, 0)},
    "Watkwal_Zwemwater_BACT": {'icon': 'meetpuntPeil.png',
                               'mask': ('meetpuntPeil_mask.png', ),
                               'color': (1.0, 0.3, 0.3, 0)},
    "Watkwal_Zwemwater_BEST": {'icon': 'meetpuntPeil.png',
                               'mask': ('meetpuntPeil_mask.png', ),
                               'color': (0, 1, 1, 0)},
    "Watkwal_Zwemwater_IONEN": {'icon': 'meetpuntPeil.png',
                                'mask': ('meetpuntPeil_mask.png', ),
                                'color': (1, 0, 1, 0)},
    "Watkwal_Zwemwater_METAL": {'icon': 'meetpuntPeil.png',
                                'mask': ('meetpuntPeil_mask.png', ),
                                'color': (0.5, 0.5, 1, 0)},
    "Watkwal_Zwemwater_NUTRI": {'icon': 'meetpuntPeil.png',
                                'mask': ('meetpuntPeil_mask.png', ),
                                'color': (1, 1, 0, 0)},
    "Watkwal_Zwemwater_PAK": {'icon': 'meetpuntPeil.png',
                              'mask': ('meetpuntPeil_mask.png', ),
                              'color': (1, 0, 1, 0)},
    "Watkwal_Zwemwater_PCB": {'icon': 'meetpuntPeil.png',
                              'mask': ('meetpuntPeil_mask.png', ),
                              'color': (0, 1, 1, 0)},
    "Watkwal_Zwemwater_REST": {'icon': 'meetpuntPeil.png',
                               'mask': ('meetpuntPeil_mask.png', ),
                               'color': (1, 1, 0, 0)},
    "Waterkwaliteit_ALG": {'icon': 'meetpuntPeil.png',
                           'mask': ('meetpuntPeil_mask.png', ),
                           'color': (0, 1.0, 0, 0)},
    "Waterkwaliteit_BACT": {'icon': 'meetpuntPeil.png',
                            'mask': ('meetpuntPeil_mask.png', ),
                            'color': (1.0, 0.3, 0.3, 0)},
    "Waterkwaliteit_BEST": {'icon': 'meetpuntPeil.png',
                            'mask': ('meetpuntPeil_mask.png', ),
                            'color': (0, 1, 1, 0)},
    "Waterkwaliteit_IONEN": {'icon': 'meetpuntPeil.png',
                             'mask': ('meetpuntPeil_mask.png', ),
                             'color': (1, 0, 1, 0)},
    "Waterkwaliteit_METAL": {'icon': 'meetpuntPeil.png',
                             'mask': ('meetpuntPeil_mask.png', ),
                             'color': (0.5, 0.5, 1, 0)},
    "Waterkwaliteit_NUTRI": {'icon': 'meetpuntPeil.png',
                             'mask': ('meetpuntPeil_mask.png', ),
                             'color': (1, 1, 0, 0)},
    "Waterkwaliteit_PAK": {'icon': 'meetpuntPeil.png',
                           'mask': ('meetpuntPeil_mask.png', ),
                           'color': (1, 0, 1, 0)},
    "Waterkwaliteit_PCB": {'icon': 'meetpuntPeil.png',
                           'mask': ('meetpuntPeil_mask.png', ),
                           'color': (0, 1, 1, 0)},
    "Waterkwaliteit_REST": {'icon': 'meetpuntPeil.png',
                            'mask': ('meetpuntPeil_mask.png', ),
                            'color': (1, 1, 0, 0)},
    }


def fews_symbol_name(filterkey, nodata=False):
    """Find fews symbol name"""

    # determine icon layout by looking at filter.id
    filter_ = get_object_or_404(Filter, pk=filterkey)
    if str(filter_.fews_id) in LAYER_STYLES:
        icon_style = copy.deepcopy(LAYER_STYLES[str(filter_.fews_id)])
    else:
        icon_style = copy.deepcopy(LAYER_STYLES['default'])

    #make icon grey
    if nodata:
        icon_style['color'] = (0.9, 0.9, 0.9, 0)

    # apply icon layout using symbol manager
    symbol_manager = SymbolManager(
        ICON_ORIGINALS,
        os.path.join(settings.MEDIA_ROOT, 'generated_icons'))
    output_filename = symbol_manager.get_symbol_transformed(
        icon_style['icon'], **icon_style)

    return output_filename


def fews_point_style(filterkey, nodata=False):
    """
    make mapnik point_style for fews point with given filterkey
    """
    output_filename = fews_symbol_name(filterkey, nodata)
    output_filename_abs = os.path.join(
        settings.MEDIA_ROOT, 'generated_icons', output_filename)

    # use filename in mapnik pointsymbolizer
    point_looks = mapnik.PointSymbolizer(output_filename_abs, 'png', 16, 16)
    point_looks.allow_overlap = True
    layout_rule = mapnik.Rule()
    layout_rule.symbols.append(point_looks)
    point_style = mapnik.Style()
    point_style.rules.append(layout_rule)

    return point_style


class WorkspaceItemAdapterFewsUnblobbed(workspace.WorkspaceItemAdapter):
    """
    Should be registered as adapter_fews
    """
    def __init__(self, *args, **kwargs):
        super(WorkspaceItemAdapterFewsUnblobbed, self).__init__(
            *args, **kwargs)
        self.filterkey = self.layer_arguments['filterkey']
        self.parameterkey = self.layer_arguments['parameterkey']

    def layer(self, layer_ids=None, webcolor=None):
        """Return layer and styles that render points.

        """
        layers = []
        styles = {}
        layer = mapnik.Layer("FEWS points layer", coordinates.RD)
        layer_nodata = mapnik.Layer("FEWS points layer (no data)",
                                    coordinates.RD)
        filterkey = self.filterkey
        parameterkey = self.parameterkey

        layer.datasource = mapnik.PointDatasource()
        layer_nodata.datasource = mapnik.PointDatasource()
        for info in self._timeseries():
            layer.datasource.add_point(
                info['rd_x'], info['rd_y'], 'Name', info['location_name'])
            # TODO: layer only points with data, but it misses some points
            if not info['has_data']:
                layer_nodata.datasource.add_point(
                    info['rd_x'], info['rd_y'], 'Name', info['location_name'])

        point_style = fews_point_style(filterkey, nodata=False)
        # generate "unique" point style name and append to layer
        style_name = "Style with data %s::%s " % (filterkey, parameterkey)
        styles[style_name] = point_style
        layer.styles.append(style_name)

        point_style_nodata = fews_point_style(filterkey, nodata=True)
        # generate "unique" point style name and append to layer
        style_name_nodata = "Style nodata %s::%s" % (filterkey, parameterkey)
        styles[style_name_nodata] = point_style_nodata
        layer_nodata.styles.append(style_name_nodata)

        layers = [layer_nodata, layer]  # TODO: the layer WITH data on top
        return layers, styles

    def _timeseries(self):
        workspace_id = self.workspace_item.workspace.id
        cache_key = 'lizard_fewsunblobbed.layers.timeseries_%s_%s_%s' % (
            workspace_id, self.filterkey, self.parameterkey)
        result = cache.get(cache_key)
        if result is None:
            result = [
                {'rd_x': timeserie.locationkey.x,
                 'rd_y': timeserie.locationkey.y,
                 'object': timeserie,
                 'location_name': str(timeserie.locationkey.name),
                 'name': timeserie.name,
                 'shortname': timeserie.shortname,
                 'workspace_item': self.workspace_item,
                 'identifier': {'locationkey': timeserie.locationkey.pk},
                 'google_coords': timeserie.locationkey.google_coords(),
                 'has_data': timeserie.has_data,
                 }
                for timeserie in
                Timeserie.objects.filter(filterkey=self.filterkey,
                                         parameterkey=self.parameterkey)]
            cache.set(cache_key, result, 8 * 60 * 60)
        return copy.deepcopy(result)

    def search(self, google_x, google_y, radius=None):
        """Return list of dict {'distance': <float>, 'timeserie':
        <timeserie>} of closest fews point that matches x, y, radius.

        """
        x, y = coordinates.google_to_rd(google_x, google_y)
        timeseries_info = self._timeseries()
        for info in timeseries_info:
            info['distance'] = sqrt((info['rd_x'] - x) ** 2 +
                                    (info['rd_y'] - y) ** 2)
        # Filter out correct distances.
        result = []
        for found_result in timeseries_info:
            if found_result['distance'] <= radius*0.3:
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
            'object': timeserie,
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

    def symbol_url(self, identifier=None, start_date=None, end_date=None):
        """
        returns symbol

        """
        output_filename = fews_symbol_name(self.filterkey, nodata=False)
        return '%sgenerated_icons/%s' % (settings.MEDIA_URL, output_filename)

    def html(self, identifiers, add_snippet=False):
        return super(WorkspaceItemAdapterFewsUnblobbed, self).html_default(
            identifiers, add_snippet=add_snippet)
