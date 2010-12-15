import os
import datetime
import copy
import logging
from math import sqrt

import mapnik
from django.conf import settings
from django.core.cache import cache
from django.db.models import Avg
from django.db.models import Min
from django.db.models import Max
from django.http import Http404
from django.shortcuts import get_object_or_404

from lizard_fewsunblobbed.models import Filter
from lizard_fewsunblobbed.models import Location
from lizard_fewsunblobbed.models import Parameter
from lizard_fewsunblobbed.models import Timeserie
from lizard_map import coordinates
from lizard_map import workspace
from lizard_map.adapter import Graph
from lizard_map.models import ICON_ORIGINALS
from lizard_map.symbol_manager import SymbolManager


logger = logging.getLogger('lizard_fewsunblobbed.layers')

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


def fews_timeserie(filterkey, locationkey, parameterkey):
    """Get fews timeserie from filter, location, parameter. Beware:
    sometimes multiple items are returned."""

    result = Timeserie.objects.filter(
        filterkey=filterkey,
        locationkey=locationkey,
        parameterkey=parameterkey)
    if len(result) == 0:
        raise Http404
    elif len(result) > 1:
        logger.warn('Multiple timeserie objects found for '
                    'filter, location, parameter = '
                    '(%s, %s, %s)' % (filterkey, locationkey, parameterkey))
    return result[0]


class WorkspaceItemAdapterFewsUnblobbed(workspace.WorkspaceItemAdapter):
    """
    Should be registered as adapter_fews
    """

    def __init__(self, *args, **kwargs):
        super(WorkspaceItemAdapterFewsUnblobbed, self).__init__(
            *args, **kwargs)
        self.filterkey = self.layer_arguments['filterkey']
        self.parameterkey = self.layer_arguments['parameterkey']

    def layer(self, layer_ids=None, webcolor=None, request=None):
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
            # print info['rd_x'], info['rd_y'], info['location_name']
            layer.datasource.add_point(
                info['rd_x'], info['rd_y'], 'Name', info['location_name'])
            # Due to mapnik bug, we render the very same point 10cm to the top
            # right, bottom left, etc.
            layer.datasource.add_point(
                info['rd_x'] + 0.1, info['rd_y'] + 0.1, 'Name', info['location_name'])
            layer.datasource.add_point(
                info['rd_x'] - 0.1, info['rd_y'] - 0.1, 'Name', info['location_name'])
            layer.datasource.add_point(
                info['rd_x'] + 0.1, info['rd_y'] - 0.1, 'Name', info['location_name'])
            # TODO: layer only points with data, but it misses some points
            if not info['has_data']:
                layer_nodata.datasource.add_point(
                    info['rd_x'], info['rd_y'], 'Name', info['location_name'])

        point_style = fews_point_style(filterkey, nodata=False)
        # generate "unique" point style name and append to layer
        style_name = "Style with data %s::%s" % (filterkey, parameterkey)
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
            for timeserie in Timeserie.objects.filter(
                filterkey=self.filterkey,
                parameterkey=self.parameterkey):
                location = locations[timeserie.locationkey_id]
                name = u'%s (%s): %s' % (parameter.name, parameter.unit,
                                         location.name)
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
                 'has_data': timeserie.has_data,
                 # ^^^ Most expensive: ~100 locs per second
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
            if found_result['distance'] <= radius * 0.3:
                result.append(found_result)

        result.sort(key=lambda item: item['distance'])
        return result

    def values(self, identifier, start_date, end_date):
        timeserie = fews_timeserie(
            self.filterkey,
            identifier['locationkey'],
            self.parameterkey)
        timeseriedata = timeserie.timeseriedata.filter(
            tsd_time__gte=start_date,
            tsd_time__lte=end_date)

        result = []
        for timeserie_row in timeseriedata:
            result.append({
                    'value': timeserie_row.tsd_value,
                    'datetime': timeserie_row.tsd_time,
                    'unit': '',  # We don't know the unit.
                    })
        return result

    def value_aggregate(self, identifier, aggregate_functions,
                        start_date, end_date):
        return super(
            WorkspaceItemAdapterFewsUnblobbed,
            self).value_aggregate_default(
            identifier, aggregate_functions, start_date, end_date)

    def location(self, locationkey=None, layout=None):
        """Return fews point representation corresponding to
        filter_id, location_id and parameter_id in same format as
        search function

        !!layout params come from the graph_edit screen, see also image(..)
        """
        timeserie = fews_timeserie(
            self.filterkey,
            locationkey,
            self.parameterkey)

        identifier = {'locationkey': timeserie.locationkey.pk}
        if layout is not None:
            identifier['layout'] = layout

        return {
            'name': timeserie.name,
            'shortname': timeserie.shortname,
            'object': timeserie,
            'workspace_item': self.workspace_item,
            'identifier': identifier,
            'google_coords': timeserie.locationkey.google_coords(),
            }

    def image(self,
              identifiers,
              start_date,
              end_date,
              width=380.0,
              height=250.0,
              layout_extra=None):
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

        def apply_layout(layout, title, y_min, y_max, legend):
            """Applies layout options. Returns title,
            y_min, y_max, graph, legend """

            if "title" in layout:
                title = layout['title']
            if "y_min" in layout:
                y_min = float(layout['y_min'])
            if "y_max" in layout:
                y_max = float(layout['y_max'])
            if "legend" in layout:
                legend = layout['legend']
            if "y_label" in layout:
                graph.axes.set_ylabel(layout['y_label'])
            if "x_label" in layout:
                graph.set_xlabel(layout['x_label'])
            return title, y_min, y_max, legend

        def apply_lines(identifier, timeseriedata):
            """Adds lines that are defined in layout. Uses function
            variable graph, line_styles."""

            layout = identifier['layout']

            if "line_min" in layout:
                aggregated = timeseriedata.aggregate(
                    Min('tsd_value'))
                graph.axes.axhline(
                    aggregated['tsd_value__min'],
                    color=line_styles[str(identifier)]['color'],
                    lw=line_styles[str(identifier)]['min_linewidth'],
                    ls=line_styles[str(identifier)]['min_linestyle'],
                    label='Minimum')
            if "line_max" in layout:
                aggregated = timeseriedata.aggregate(
                    Max('tsd_value'))
                graph.axes.axhline(
                    aggregated['tsd_value__max'],
                    color=line_styles[str(identifier)]['color'],
                    lw=line_styles[str(identifier)]['max_linewidth'],
                    ls=line_styles[str(identifier)]['max_linestyle'],
                    label='Maximum')
            if "line_avg" in layout:
                aggregated = timeseriedata.aggregate(
                    Avg('tsd_value'))
                graph.axes.axhline(
                    aggregated['tsd_value__avg'],
                    color=line_styles[str(identifier)]['color'],
                    lw=line_styles[str(identifier)]['avg_linewidth'],
                    ls=line_styles[str(identifier)]['avg_linestyle'],
                    label='Gemiddelde')

        line_styles = self.line_styles(identifiers)

        today = datetime.datetime.now()
        graph = Graph(start_date, end_date,
                      width=width, height=height, today=today)
        graph.axes.grid(True)

        # Draw graph lines with extra's
        title = None
        y_min, y_max = None, None
        legend = None
        for identifier in identifiers:
            # Find database object that contains the timeseries data.
            timeserie = fews_timeserie(
                self.filterkey,
                identifier['locationkey'],
                self.parameterkey)
            timeseriedata = timeserie.timeseriedata.filter(
                tsd_time__gte=start_date,
                tsd_time__lte=end_date)

            # Plot data.
            dates = []
            values = []
            for series_row in timeseriedata:
                dates.append(series_row.tsd_time)
                values.append(series_row.tsd_value)
            graph.axes.plot(dates, values,
                            lw=1,
                            color=line_styles[str(identifier)]['color'],
                            label=timeserie.name)

            # Apply custom layout parameters.
            if 'layout' in identifier:
                layout = identifier['layout']
                title, y_min, y_max, legend = apply_layout(
                    layout, title, y_min, y_max, legend)
                apply_lines(identifier, timeseriedata)

        if y_min is None:
            y_min, _ = graph.axes.get_ylim()
        if y_max is None:
            _, y_max = graph.axes.get_ylim()

        # Extra layout parameters.
        if layout_extra:
            title, y_min, y_max, legend = apply_layout(
                layout_extra, title, y_min, y_max, legend)

        if title:
            graph.suptitle(title)
        graph.axes.set_ylim(y_min, y_max)

        if legend:
            graph.legend()

        graph.add_today()
        return graph.http_png()

    def symbol_url(self, identifier=None, start_date=None, end_date=None):
        """
        returns symbol

        """
        output_filename = fews_symbol_name(self.filterkey, nodata=False)
        return '%sgenerated_icons/%s' % (settings.MEDIA_URL, output_filename)

    def html(self, snippet_group=None, identifiers=None, layout_options=None):
        return super(WorkspaceItemAdapterFewsUnblobbed, self).html_default(
            snippet_group=snippet_group,
            identifiers=identifiers,
            layout_options=layout_options)
