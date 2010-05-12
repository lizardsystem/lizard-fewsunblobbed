from math import sqrt

import pkg_resources
import mapnik
#from django.conf import settings

from lizard_fewsunblobbed.models import Location
from lizard_fewsunblobbed.models import Timeserie

PLUS_ICON = pkg_resources.resource_filename('lizard_fewsunblobbed', 'add.png')


def fews_points_layer(filterkey=None, parameterkey=None):
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

    point_looks = mapnik.PointSymbolizer(PLUS_ICON, 'png', 32, 32)
    point_looks.allow_overlap = True
    layout_rule = mapnik.Rule()
    layout_rule.symbols.append(point_looks)
    point_style = mapnik.Style()
    point_style.rules.append(layout_rule)
    styles['Point style'] = point_style
    layer.styles.append('Point style')
    layers = [layer]
    return layers, styles


def fews_points_layer_search(x, y, radius=None,
                             filterkey=None, parameterkey=None):
    """Return fews points that match x, y, radius."""
    if filterkey is None and parameterkey is None:
        # Grab the first 1000 locations
        locations = Location.objects.all()[:1000]
    else:
        locations = [timeserie.locationkey for timeserie in
                     Timeserie.objects.filter(filterkey=filterkey,
                                              parameterkey=parameterkey)]

    distances = [(location,
                  sqrt((location.x - x) ** 2 + (location.y - y) ** 2))
                 for location in locations]
    distances.sort(key=lambda item: item[1])
    # For the time being: return the closest one.
    return [distances[0][0]]
