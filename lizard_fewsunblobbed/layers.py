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

from lizard_fewsunblobbed.models import IconStyle
from lizard_fewsunblobbed.models import Filter
from lizard_fewsunblobbed.models import Location
from lizard_fewsunblobbed.models import Parameter
from lizard_fewsunblobbed.models import Timeserie
from lizard_map import coordinates
from lizard_map import workspace
from lizard_map.adapter import Graph
from lizard_map.models import ICON_ORIGINALS
from lizard_map.models import WorkspaceItemError
from lizard_map.symbol_manager import SymbolManager
from lizard_map.mapnik_helper import add_datasource_point


logger = logging.getLogger(
    'lizard_fewsunblobbed.layers')  # pylint: disable=C0103, C0301

EPSILON = 0.0001
# maps filter ids to icons
# TODO: remove from this file to a generic place
LAYER_STYLES = {
    "default": {'icon': 'meetpuntPeil.png',
                'mask': ('meetpuntPeil_mask.png', ),
                'color': (0, 0, 1, 0)},
    # Demo. RWS, HHNK, gemeente
    "Grondwater": {
        'icon': 'meetpuntPeil.png',
        'mask': ('meetpuntPeil_mask.png', ),
        'color': (1, 0.5, 0.5, 0)},
    "Kusten en rivieren": {
        'icon': 'buoy.png',
        'mask': ('buoy_mask.png', ),
        'color': (1, 0.2, 1, 0)},  # RWS
    "Meteo": {
        'icon': 'neerslagstation.png',
        'mask': ('neerslagstation_mask.png', ),
        'color': (0.5, 0.5, 1, 0)},
    "Oppervlaktewater": {
        'icon': 'gemaal.png',
        'mask': ('gemaal_mask.png', ),
        'color': (0, 0, 1, 0)},  # HHNK
    "Riolering": {
        'icon': 'rioolgemaal.png',
        'mask': ('rioolgemaal_mask.png', ),
        'color': (0, 1, 0, 0)},
    "Waterkwaliteit": {
        'icon': 'meetpuntBWS.png',
        'mask': ('meetpuntBWS_mask.png', ),
        'color': (0, 0, 1, 0)},  # HHNK
    # KRW waternet
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


def fews_symbol_name(
    fews_filter_pk, fews_location_pk, fews_parameter_pk,
    nodata=False, styles=None, lookup=None):

    """Find fews symbol name"""

    # determine icon layout by looking at filter.id
    # if str(fews_filter.fews_id) in LAYER_STYLES:
    #     icon_style = copy.deepcopy(LAYER_STYLES[str(fews_filter.fews_id)])
    # else:
    #     icon_style = copy.deepcopy(LAYER_STYLES['default'])
    style_name, icon_style = IconStyle.style(
        fews_filter_pk, fews_location_pk, fews_parameter_pk, styles, lookup)

    #make icon grey
    if nodata:
        icon_style['color'] = (0.9, 0.9, 0.9, 0)

    # apply icon layout using symbol manager
    symbol_manager = SymbolManager(
        ICON_ORIGINALS,
        os.path.join(settings.MEDIA_ROOT, 'generated_icons'))
    output_filename = symbol_manager.get_symbol_transformed(
        icon_style['icon'], **icon_style)

    return style_name, output_filename


def fews_point_style(
    fews_filter, fews_location,
    fews_parameter, nodata=False, styles=None, lookup=None):
    """
    make mapnik point_style for fews point with given filterkey
    """
    point_style_name, output_filename = fews_symbol_name(
        fews_filter.pk, fews_location.pk, fews_parameter.pk,
        nodata, styles, lookup)
    output_filename_abs = os.path.join(
        settings.MEDIA_ROOT, 'generated_icons', output_filename)

    # use filename in mapnik pointsymbolizer
    point_looks = mapnik.PointSymbolizer(
        str(output_filename_abs), 'png', 16, 16)
    point_looks.allow_overlap = True
    layout_rule = mapnik.Rule()
    layout_rule.symbols.append(point_looks)

    point_style = mapnik.Style()
    point_style.rules.append(layout_rule)

    return point_style_name, point_style


def fews_timeserie(filterkey, locationkey, parameterkey):
    """Get fews timeserie from filter, location, parameter. Beware:
    sometimes multiple items are returned."""

    result = Timeserie.objects.filter(
        filterkey=filterkey,
        locationkey=locationkey,
        parameterkey=parameterkey)
    if len(result) == 0:
        raise Http404(
            "Timeserie for filter %s, location %s, param %s not found." % (
                filterkey, locationkey, parameterkey))
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
        perform_existence_verification = kwargs.pop(
            'perform_existence_verification', True)
        super(WorkspaceItemAdapterFewsUnblobbed, self).__init__(
            *args, **kwargs)
        self.filterkey = self.layer_arguments['filterkey']
        self.parameterkey = self.layer_arguments['parameterkey']
        if perform_existence_verification:
            # ^^^ TODO: hack for testing, needs better solution.
            self.verify_existence()

    def verify_existence(self):
        """Raise WorkspaceItemError if we don't exist."""
        try:
            Filter.objects.get(pk=self.filterkey)
        except Filter.DoesNotExist:
            raise WorkspaceItemError(
                "Filter %s not found" % self.filterkey)
        try:
            Parameter.objects.get(pk=self.parameterkey)
        except Parameter.DoesNotExist:
            raise WorkspaceItemError(
                "Parameter %s not found" % self.parameterkey)

    def layer(self, layer_ids=None, webcolor=None, request=None):
        """Return layer and styles that render points."""
        layers = []
        styles = {}
        styles_nodata = {}
        styles_data = {}
        layer = mapnik.Layer("FEWS points layer", coordinates.WGS84)
        layer_nodata = mapnik.Layer("FEWS points layer (no data)",
                                    coordinates.WGS84)
        filterkey = self.filterkey
        parameterkey = self.parameterkey
        #fews_filter = Filter.objects.get(pk=filterkey)
        #fews_parameter = Parameter.objects.get(pk=parameterkey)

        layer.datasource = mapnik.PointDatasource()
        layer_nodata.datasource = mapnik.PointDatasource()

        fews_styles, fews_style_lookup = IconStyle._styles_lookup()

        for info in self._timeseries():
            # Due to mapnik bug, we render the very same point 10cm to the top
            # right, bottom left, etc.
            add_datasource_point(
                layer.datasource, info['longitude'], info['latitude'],
                'Name', info['location_name'])

            if not info['has_data']:
                add_datasource_point(
                    layer_nodata.datasource,
                    info['longitude'], info['latitude'],
                    'Name', info['location_name'])

            point_style_name, point_style = fews_point_style(
                info['object'].filterkey, info['object'].locationkey,
                info['object'].parameterkey, nodata=False, styles=fews_styles,
                lookup=fews_style_lookup)
            # generate "unique" point style name and append to layer
            style_name = "fews-unblobbed::%s" % point_style_name
            styles_data[style_name] = point_style

            point_style_nodata_name, point_style_nodata = fews_point_style(
                info['object'].filterkey, info['object'].locationkey,
                info['object'].parameterkey, nodata=True, styles=fews_styles,
                lookup=fews_style_lookup)
            # generate "unique" point style name and append to layer
            style_name_nodata = "fews-unblobbed-nodata::%s" % (
                point_style_nodata_name)
            styles[style_name_nodata] = point_style_nodata  # to return
            styles_nodata[style_name_nodata] = point_style_nodata  # for layer

        for style_name in styles_data.keys():
            layer.styles.append(style_name)

        for style_name_nodata in styles_nodata.keys():
            layer_nodata.styles.append(style_name_nodata)

        styles = styles_data
        styles.update(styles_nodata)

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

            # Pre load all used locations in a dictionary.
            # In some cases it takes 3 seconds?
            locations = dict([(location.pk, location)
                              for location in Location.objects.filter(
                        timeserie__filterkey=self.filterkey)])
            result = []
            related_timeseries = list(Timeserie.objects.filter(
                    filterkey=self.filterkey,
                    parameterkey=self.parameterkey))

            # Fetch cached has_data dict for all timeseries.
            timeseries_has_data = Timeserie.has_data_dict()
            for timeserie in related_timeseries:
                location = locations[timeserie.locationkey_id]
                name = u'%s (%s): %s' % (parameter.name, parameter.unit,
                                         location.name)
                shortname = u'%s' % location.name
                result.append(
                {'rd_x': location.x,
                 'rd_y': location.y,
                 'longitude': location.longitude,
                 'latitude': location.latitude,
                 'object': timeserie,
                 'location_name': location.name.encode('ascii', 'replace'),
                 # ^^^ This used to be ``str(location.name)``.
                 # Which fails on non-ascii input.
                 # TODO: does it really need to be a string?
                 # It seems to be proper unicode to begin with.
                 'name': name,
                 'shortname': shortname,
                 'workspace_item': self.workspace_item,
                 'identifier': {'locationkey': location.pk},
                 'google_coords': location.google_coords(),
                 'has_data': timeserie.pk in timeseries_has_data,
                 })
            cache.set(cache_key, result, 8 * 60 * 60)
        else:
            # the workspace_item can be different, so overwrite with our own
            for row in result:
                row['workspace_item'] = self.workspace_item
        return copy.deepcopy(result)

    def extent(self, identifiers=None):
        """Return extent."""
        north = None
        south = None
        east = None
        west = None

        wgs0coord_x, wgs0coord_y = coordinates.rd_to_wgs84(0.0, 0.0)
        for info in self._timeseries():
            x = info['rd_x']
            y = info['rd_y']
            # Ignore rd coordinates (0, 0).
            if (abs(x - wgs0coord_x) > EPSILON or
                abs(y - wgs0coord_y) > EPSILON):

                if x > east or east is None:
                    east = x
                if x < west or west is None:
                    west = x
                if y < south or south is None:
                    south = y
                if y > north or north is None:
                    north = y

        west_transformed, north_transformed = coordinates.rd_to_google(
            west, north)
        east_transformed, south_transformed = coordinates.rd_to_google(
            east, south)
        return {
            'north': north_transformed,
            'west': west_transformed,
            'south': south_transformed,
            'east': east_transformed}

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
        timeseriedata = timeserie.timeseriedata.order_by("tsd_time").filter(
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
            timeseriedata = timeserie.timeseriedata.order_by(
                "tsd_time").filter(
                tsd_time__gte=start_date,
                tsd_time__lte=end_date)

            # Plot data.
            dates = []
            values = []
            for series_row in timeseriedata:
                dates.append(series_row.tsd_time)
                values.append(series_row.tsd_value)
            if len(values) < 30:
                plot_style = 'o-'
            else:
                plot_style = '-'
            graph.axes.plot(dates, values, plot_style,
                            lw=1,
                            color=line_styles[str(identifier)]['color'],
                            label=timeserie.name)
            graph.axes.set_ylabel(timeserie.parameterkey.unit)

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
            # Place legend on top op graph, no borders.
            graph.legend()
            graph.axes.legend_.draw_frame(False)

        if "horizontal_lines" in layout_extra:
            for horizontal_line in layout_extra['horizontal_lines']:
                graph.axes.axhline(
                    horizontal_line['value'],
                    ls=horizontal_line['style']['linestyle'],
                    color=horizontal_line['style']['color'],
                    lw=horizontal_line['style']['linewidth'],
                    label=horizontal_line['name'])

        graph.add_today()
        return graph.http_png()

    def symbol_url(self, identifier=None, start_date=None, end_date=None):
        """
        returns symbol

        TODO: fill identifier from caller.
        """
        point_style_name, output_filename = fews_symbol_name(
            self.filterkey, None, self.parameterkey,
            nodata=False)

        # output_filename = fews_symbol_name(
        #     self.filterkey,
        #     nodata=False)

        return '%sgenerated_icons/%s' % (settings.MEDIA_URL, output_filename)

    def html(self, snippet_group=None, identifiers=None, layout_options=None):
        return super(WorkspaceItemAdapterFewsUnblobbed, self).html_default(
            snippet_group=snippet_group,
            identifiers=identifiers,
            layout_options=layout_options)
