# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
# $Id: dummy.py 27497 2012-05-04 12:47:47Z erikjan.vos $

class IconStyle(object):
    @classmethod
    def _styles_lookup(cls, ignore_cache=False):
        return {}, {}

    @classmethod
    def style(
        cls,
        fews_filter_pk,
        fews_location_pk, fews_parameter_pk,
        styles=None, lookup=None, ignore_cache=False):
        return '::::', {
            'icon': 'meetpuntPeil.png',
            'mask': ('meetpuntPeil_mask.png', ),
            'color': (0.0, 0.5, 1.0, 1.0)
            }
