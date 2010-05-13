import os
from math import sqrt

import pkg_resources
import mapnik
from django.conf import settings
from django.shortcuts import get_object_or_404

from lizard_fewsunblobbed.models import Location
from lizard_fewsunblobbed.models import Timeserie
from lizard_fewsunblobbed.models import Filter

from lizard_map.symbol_manager import SymbolManager
from lizard_map.views import ICON_ORIGINALS

PLUS_ICON = pkg_resources.resource_filename('lizard_fewsunblobbed', 'add.png')

# maps filter ids to icons
# TODO: remove from this file to a generic place
LAYER_STYLES = {
    "default": {'icon': 'meetpuntPeil.png', 'mask': ('meetpuntPeil_mask.png', ), 'color': (1,1,1,0)},
    "boezem_waterstanden": {'icon': 'meetpuntPeil.png', 'mask': ('meetpuntPeil_mask.png', ), 'color': (0,0.5,1,0)},
    "boezem_meetpunt": {'icon': 'meetpuntPeil.png', 'mask': ('meetpuntPeil_mask.png', ), 'color': (0,1,0,0)},
    "boezem_poldergemaal": {'icon': 'gemaal.png', 'mask': ('gemaal_mask.png', ), 'color': (0,1,0,0)},
    "west_opvoergemaal": {'icon': 'gemaal.png', 'mask': ('gemaal_mask.png', ), 'color': (1,0,1,0)},
    "west_stuw_(hand)": {'icon': 'stuw.png', 'mask': ('stuw_mask.png', ), 'color': (0,1,0,0)},
    "west_stuw_(auto)": {'icon': 'stuw.png', 'mask': ('stuw_mask.png', ), 'color': (1,0,0,0)},
    "oost_stuw_(hand)": {'icon': 'stuw.png', 'mask': ('stuw_mask.png', ), 'color': (0,1,0,0)},
    "oost_stuw_(auto)": {'icon': 'stuw.png', 'mask': ('stuw_mask.png', ), 'color': (1,0,0,0)},
    "west_hevel": {'icon': 'hevel.png', 'mask': ('hevel_mask.png', ), 'color': (1,1,0,0)},
    "waterketen_rioolgemalen": {'icon': 'gemaal.png', 'mask': ('gemaal_mask.png', ), 'color': (0.7,0.5,0,0)},
    "waterketen_overstorten": {'icon': 'overstort.png', 'mask': ('overstort_mask.png', ), 'color': (1,1,1,0)},
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
    symbol_manager = SymbolManager(ICON_ORIGINALS, os.path.join(settings.MEDIA_ROOT, 'generated_icons'))
    output_filename = symbol_manager.get_symbol_transformed(icon_style['icon'], **icon_style)

    return output_filename


def fews_points_layer(filterkey=None, parameterkey=None, webcolor=None):
    """Return layer and styles that render points.

    Registered as ``fews_points_layer``
    """
    layers = []
    styles = {}
    layer = mapnik.Layer(
        "FEWS points layer",
        ("+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 "
         "+k=0.999908 +x_0=155000 +y_0=463000 +ellps=bessel "
         "+towgs84=565.237,50.0087,465.658,-0.406857,0.350733,-1.87035,4.0812 "
         "+units=m +no_defs"))
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
        layer.datasource.add_point(location.x, location.y, 'Name', str(location.name))

    output_filename = fews_symbol_name(filterkey)
    output_filename_abs = os.path.join(settings.MEDIA_ROOT, 'generated_icons', output_filename)

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


def fews_points_layer_search(x, y, radius=None,
                             filterkey=None, parameterkey=None):
    """Return fews points that match x, y, radius."""
    # TODO: x, y isn't in the correct projection, I think.  [reinout]
    distances = [(timeserie,
                  sqrt((timeserie.locationkey.x - x) ** 2 +
                       (timeserie.locationkey.y - y) ** 2))
                 for timeserie in
                 Timeserie.objects.filter(filterkey=filterkey,
                                          parameterkey=parameterkey)]
    distances.sort(key=lambda item: item[1])
    # For the time being: return the closest one.
    return [distances[0]]
