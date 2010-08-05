import os
import datetime
import copy
from math import sqrt

import mapnik
from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db.models import Avg
from django.db.models import Min
from django.db.models import Max
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from matplotlib.lines import Line2D
import simplejson as json

from lizard_fewsunblobbed.models import Filter
from lizard_fewsunblobbed.models import Location
from lizard_fewsunblobbed.models import Parameter
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
        """
        Get list of dicts of all timeseries. Optimized for performance.
        """
        cache_key = 'lizard_fewsunblobbed.layers.timeseries_%s_%s' % (
            self.filterkey, self.parameterkey)
        result = cache.get(cache_key)
        if result is None:
            # fetching locationkey and parameterkey seems to be very expensive
            parameter = Parameter.objects.get(pk=self.parameterkey)

            # pre load all used locations in a dictionary ! < 1 sec
            locations = dict([(location.pk, location) \
                                  for location in Location.objects.filter(
                        timeserie__filterkey=self.filterkey)])
            result = []
            for timeserie in Timeserie.objects.filter(filterkey=self.filterkey,
                                                      parameterkey=self.parameterkey):
                location = locations[timeserie.locationkey_id]
                name = u'%s (%s): %s' % (parameter.name, parameter.unit, location)
                shortname = u'%s' % location.name
                result.append(
                {'rd_x': location.x,
                 'rd_y': location.y,
                 'object': timeserie,
                 'location_name': str(location.name),
                 'name': name,
                 'shortname': shortname,
                 'workspace_item': self.workspace_item,
                 'identifier': {'locationkey': location.pk},
                 'google_coords': location.google_coords(),
                 'has_data': timeserie.has_data,  # most expensive ~100 locs per second
                 })
            cache.set(cache_key, result, 8 * 60 * 60)
        else:
            # the workspace_item can be different, so overwrite with our own
            for row in result:
                row['workspace_item'] = self.workspace_item
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

    def location(self, locationkey=None, layout=None):
        """Return fews point representation corresponding to
        filter_id, location_id and parameter_id in same format as
        search function

        !!layout params come from the graph_edit screen, see also image(..)
        """
        timeserie = get_object_or_404(
            Timeserie,
            filterkey=self.filterkey,
            locationkey=locationkey,
            parameterkey=self.parameterkey)

        identifier = {'locationkey': timeserie.locationkey.pk}
        if layout is not None:
            identifier['layout'] = layout

        # We want to combine workspace_item and identifier into get_absolute_url
        timeserie.get_absolute_url = reverse(
            'lizard_map.workspace_item.graph_edit',
            kwargs={'workspace_item_id': self.workspace_item.id}
            )
        timeserie.get_absolute_url += '?identifier=%s' % (json.dumps(identifier).replace('"', '%22'))

        return {
            'name': timeserie.name,
            'shortname': timeserie.shortname,
            'object': timeserie,
            'workspace_item': self.workspace_item,
            'identifier': identifier,
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

        note: in a identifier extra parameters can be set to control
        image behaviour.

        extra parameters in 'layout': y_min, y_max, line_min,
        line_max, line_avg, title, y_label, x_label, colors. the
        colors attribute is a single string, colors are splitted by a
        space ' '.
        """
        series = []
        color_list = None
        for identifier in identifier_list:
            timeserie = get_object_or_404(Timeserie,
                                          locationkey=identifier['locationkey'],
                                          filterkey=self.filterkey,
                                          parameterkey=self.parameterkey)
            timeseriedata = timeserie.timeseriedata.filter(tsd_time__gte=start_date,
                                                           tsd_time__lte=end_date)
            if 'layout' in identifier:
                if 'colors' in identifier['layout']:
                    color_list = identifier['layout']['colors'].split()
            series.append({
                    'identifier': identifier,
                    'timeserie': timeserie,
                    'timeseriedata': timeseriedata,
                    })

        # Default color list
        if color_list is None:
            color_list = ['blue', 'green', 'cyan', 'magenta', 'black']

        today = datetime.datetime.now()

        graph = Graph(start_date, end_date,
                      width=width, height=height, today=today)

        graph.axes.grid(True)

        # Draw the actual graph lines
        for index, single_series in enumerate(series):
            dates = []
            values = []
            for data in single_series['timeseriedata']:
                dates.append(data.tsd_time)
                values.append(data.tsd_value)
            graph.axes.plot(dates, values,
                            lw=1,
                            color=color_list[index % len(color_list)])

        # Extra layout parameters: title, axes, extra lines, ...
        title = None
        y_min, y_max = graph.axes.get_ylim()
        legend = None
        for series_index, single_series in enumerate(series):
            identifier = single_series['identifier']
            if 'layout' in identifier:
                layout = identifier['layout']
                if "title" in layout:
                    title = layout['title']
                if "y_min" in layout:
                    y_min = float(layout['y_min'])
                if "y_max" in layout:
                    y_max = float(layout['y_max'])
                if "line_min" in layout:
                    aggregated = single_series['timeseriedata'].aggregate(Min('tsd_value'))
                    graph.axes.axhline(aggregated['tsd_value__min'], color='green',
                                       lw=3, label='Minimum')
                if "line_max" in layout:
                    aggregated = single_series['timeseriedata'].aggregate(Max('tsd_value'))
                    graph.axes.axhline(aggregated['tsd_value__max'], color='green',
                                       lw=3, label='Maximum')
                if "line_avg" in layout:
                    aggregated = single_series['timeseriedata'].aggregate(Avg('tsd_value'))
                    graph.axes.axhline(aggregated['tsd_value__avg'], color='green',
                                       lw=3, label='Gemiddelde')
                if "legend" in layout:
                    legend = layout['legend']
                if "y_label" in layout:
                    graph.axes.set_ylabel(layout['y_label'])
                if "x_label" in layout:
                    graph.set_xlabel(layout['x_label'])

        # Title.
        if title is None:
            if len(series) <= 1:
                title = '/'.join([single_series['timeserie'].name
                                  for single_series in series])
            else:
                title = 'multiple graphs'
        graph.suptitle(title)
        graph.axes.set_ylim(y_min, y_max)

        if legend:
            handles, labels = graph.axes.get_legend_handles_labels()
            for index, single_series in enumerate(series):
                handles.append(Line2D([], [], color=color_list[index % len(color_list)], lw=1))
                labels.append('Waarde')

            graph.legend(handles, labels)

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
