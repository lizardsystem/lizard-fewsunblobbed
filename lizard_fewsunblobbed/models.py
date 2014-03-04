# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
# $Id$

import logging
from django.conf import settings
from django.core import serializers
from django.core.cache import cache
from django.db import models
from django.utils.translation import ugettext as _

from treebeard.al_tree import AL_Node
from lizard_map import coordinates
from lizard_security.manager import FilteredManager
from lizard_security.models import DataSet


logger = logging.getLogger(__name__)


PARAMETER_CACHE_KEY = 'lizard.fewsunblobbed.models.parameter_cache_key::%s'


class Filter(AL_Node):
    """Fews filter object."""

    # treebeard expects (hardcoded) fields 'id' and 'parent', while
    # fews exposes fkey and parentfkey.
    id = models.IntegerField(primary_key=True, db_column='fkey')
    # since 'id' is already used, we remap 'id' to 'fews_id'.
    fews_id = models.CharField(max_length=64, unique=True, db_column='id')
    name = models.CharField(max_length=256, blank=True)
    description = models.CharField(max_length=256, blank=True)
    issubfilter = models.BooleanField()
    # treebeard requirement (see 'id')
    parent = models.ForeignKey('Filter', null=True, blank=True,
                               db_column='parentfkey')
    isendnode = models.BooleanField()
    data_set = models.ForeignKey(DataSet,
                                 null=True,
                                 blank=True)

    node_order_by = ['name']
    objects = FilteredManager()

    class Meta:
        verbose_name = _("Filter")
        verbose_name_plural = _("Filters")
        db_table = u'filter'

    def __unicode__(self):
        return u'%s (id=%s)' % (self.name, self.fews_id)

    @property
    def has_parameters(self):
        """Return whether there is at least one connected timeserie.

        Note: parameters of descendants are not counted."""
        return Timeserie.objects.filter(filterkey=self.id).exists()

    def parameters(self):
        """Return parameters for this filter and the filters children.

        The parameters returned have an added property 'filterkey'.
        """
        parameter_cache_key = PARAMETER_CACHE_KEY % str(self.id)
        parameters = cache.get(parameter_cache_key)
        if parameters is None:
            parameters = []  # Start new one
            # Fetch all filter -> parameter combinations.
            for f in [self] + self.get_descendants():
                for p in Parameter.objects.filter(
                    timeserie__filterkey=f).distinct():

                    # Add filterkey for use in template (it's a m2m).
                    p.filterkey = f
                    if f != self:
                        p.name = '%s (%s)' % (p.name, f.name)
                    parameters.append(p)

            # parameters = param_dict.values()
            parameters.sort(key=lambda p: p.name)
            cache.set(parameter_cache_key, parameters, 8 * 60 * 60)

        return parameters

    @classmethod
    def get_database_engine(cls):
        """Overriding treebeard: it grabs the 'default' database engine."""
        engine = settings.DATABASES['fews-unblobbed']['ENGINE']
        return engine.split('.')[-1]

    # This method is overriden from the class AL_Node in al_tree.py from the
    # django-treebeard application.  The method fixes checks first if the
    # field sib_order exist before deleting, which the original version
    # doesn't do (which causes a bug).

    @classmethod
    def dump_bulk(cls, parent=None, keep_ids=True):
        """
        Dumps a tree branch to a python data structure.

        See: :meth:`treebeard.Node.dump_bulk`
        """

        # not really a queryset, but it works
        qset = cls.get_tree(parent)

        ret, lnk = [], {}
        pos = 0
        for pyobj in serializers.serialize('python', qset):
            node = qset[pos]
            depth = node.get_depth()
            # django's serializer stores the attributes in 'fields'
            fields = pyobj['fields']
            del fields['parent']
            if 'sib_order' in fields:
                del fields['sib_order']
            if 'id' in fields:
                del fields['id']
            fields['has_parameters'] = node.has_parameters
            newobj = {'data': fields}
            if keep_ids:
                newobj['id'] = pyobj['pk']

            if ((not parent and depth == 1) or
                (parent and depth == parent.get_depth())):
                ret.append(newobj)
            else:
                parentobj = lnk[node.parent_id]
                if 'children' not in parentobj:
                    parentobj['children'] = []
                parentobj['children'].append(newobj)
            lnk[node.id] = newobj
            pos += 1
        return ret


class Location(models.Model):
    """Fews location object.
    """

    lkey = models.IntegerField(primary_key=True)
    id = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=256, blank=True)
    parentid = models.CharField(max_length=64, blank=True)
    description = models.CharField(max_length=256, blank=True)
    shortname = models.CharField(max_length=256, blank=True)
    tooltiptext = models.CharField(max_length=1000, blank=True)
    x = models.FloatField(blank=True)
    y = models.FloatField(blank=True)
    z = models.FloatField(blank=True)
    longitude = models.FloatField(blank=True)
    latitude = models.FloatField(blank=True)

    class Meta:
        verbose_name = _("Location")
        verbose_name_plural = _("Locations")
        db_table = u'location'

    def __unicode__(self):
        return u'%s (lkey=%s)' % (self.name, self.lkey)

    def google_coords(self):
        return coordinates.rd_to_google(self.x, self.y)


class Parameter(models.Model):
    """Fews parameter object."""

    pkey = models.IntegerField(primary_key=True)
    id = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=256, blank=True)
    shortname = models.CharField(max_length=256, blank=True)
    unit = models.CharField(max_length=64, blank=True)
    parametertype = models.CharField(max_length=64, blank=True)
    parametergroup = models.CharField(max_length=64, blank=True)

    class Meta:
        verbose_name = _("Parameter")
        verbose_name_plural = _("Parameters")
        db_table = u'parameter'

    def __unicode__(self):
        return u'%s (pkey=%s)' % (self.name, self.pkey)


class Timeserie(models.Model):
    """Fews timeserie object. Specifies a time series of a specific parameter.

    Examples of parameters are water discharge, zinc concentration and chloride
    concentration.

    To get to the events that belong to the current Timeserie, use the implicit
    attribute 'timeseriedata', which is a Manager for the events.
    """

    tkey = models.IntegerField(primary_key=True)
    moduleinstanceid = models.CharField(max_length=64, blank=True)
    timestep = models.CharField(max_length=64, blank=True)
    filterkey = models.ForeignKey(Filter, db_column='filterkey')
    locationkey = models.ForeignKey(Location, db_column='locationkey')
    parameterkey = models.ForeignKey(Parameter, db_column='parameterkey')

    class Meta:
        verbose_name = _("Timeserie")
        verbose_name_plural = _("Timeseries")
        db_table = u'timeserie'

    def __unicode__(self):
        return u'%s: %s' % (self.locationkey.name, self.parameterkey.name)

    @property
    def name(self):
        """Return name for use in graph legends"""
        return u'%s (%s): %s' % (self.parameterkey.name,
                                self.parameterkey.unit,
                                self.locationkey.name)

    @property
    def shortname(self):
        """Return name for use in graph legends"""
        return u'%s' % (self.locationkey.name)

    def data_count(self):
        return self.timeseriedata.all().count()

    @classmethod
    def has_data_dict(cls, ignore_cache=False):
        """
        Return for each timeserie id if it has data.

        If a timeserie has data, its id is listed in the returned
        dict. Handy when looping over great amounts of timeseries.
        """
        cache_key = 'lizard_fewsunblobbed.models.timeserie_hasdata'
        result = cache.get(cache_key)
        if result is None or ignore_cache:
            logger.info('Populating Timeserie.has_data_dict...')
            tsd = Timeseriedata.objects.all().values('tkey').distinct()
            tsd_dict = {}
            for row in tsd:
                tsd_dict[row['tkey']] = None  # Just make an entry
            cache.set(cache_key, tsd_dict, 8 * 60 * 60)
            result = tsd_dict
        return result

    @property
    def has_data(self):
        """
        Return true if this timeserie has data, false otherwise.

        Uses has_data_dict index.
        """
        if self.pk in self.has_data_dict():
            return True
        else:
            return False
        # too slow
        #return self.timeseriedata.exists()


class Timeseriedata(models.Model):
    """Fews timeseriedata object. Specifies the value of a parameter at
    a specific time.

    Note that a WaterbalanceTimeserieData does not specify the parameter
    itself, only its value at a specific time.

    Instance variables:
      * value *
        value of the parameter
      * time *
        time at which the value was measured
      * timeserie *
        link to the time serie

    ..todo::

      lizard_fewsunblobbeb.Timeseriedata has two primary keys although Django
      does not support multiple primary keys. This means that we can use this
      model to read from a FEWS unblobbed database but not write to.

      http://code.djangoproject.com/ticket/373 describes the lack of support
      for multiple keys and also a workaround.

      One example where this will affect you is when you try to create and save
      a Timeseriedata programmatically. Django will report

        ValidationError: [u'Enter a valid date/time in YYYY-MM-DD
        HH:MM[:ss[.uuuuuu]] format.']

      because it has to work with a dictionarity of values - the two primary
      keys - where it expects a single value.

      This issue is also reported in Trac in ticket:2590 and ticket:2674.

    """
    tkey = models.ForeignKey(Timeserie,
                             db_column='tkey',
                             related_name='timeseriedata')

    # ^^^ TODO: this is mighty slow in the django admin.  It grabs all the
    # timeserie names/ids.
    tsd_time = models.DateTimeField(db_column='tsd_time')
    tsd_value = models.FloatField(blank=True)
    tsd_flag = models.IntegerField(blank=True)
    tsd_detection = models.BooleanField()
    tsd_comments = models.CharField(max_length=256, blank=True)

    class Meta:
        verbose_name = _("Timeserie data")
        verbose_name_plural = _("Timeseries data")
        db_table = u'timeseriedata'
        unique_together = (('tkey', 'tsd_time'), )

    def __unicode__(self):
        return u'Data for %s: %s = %s' % (self.tkey,
                                          self.tsd_time,
                                          self.tsd_value)


class IconStyle(object):  # Used to superclass models.Model
    """
    Customizable icon styles where all "selector fields" are optional.

    The styles are cached for performance.

    Based on lizard_fewsjdbc.models.IconStyle
    """
    CACHE_KEY = 'lizard_fewsunblobbed.IconStyle'

    # Selector fields.
    #fews_filter = models.ForeignKey(Filter, null=True, blank=True)
    #fews_location = models.ForeignKey(Location, null=True, blank=True)
    #fews_parameter = models.ForeignKey(Parameter, null=True, blank=True)

    # Icon properties.
    #icon = models.CharField(max_length=40, choices=list_image_file_names())
    #mask = models.CharField(max_length=40, choices=list_image_file_names())
    #color = ColorField(help_text="Use color format fffff or 333333")

    #class Meta:
    #    verbose_name = _("Icon style")
    #    verbose_name_plural = _("Icon styles")

    #def __unicode__(self):
    #    return u'%s' % (self._key)

    #@property
    #def _key(self):
    #    return '%s::%s::%s' % (
    #        self.fews_filter.pk if self.fews_filter else '',
    #        self.fews_location.pk if self.fews_location else '',
    #        self.fews_parameter.pk if self.fews_parameter else '')

    @classmethod
    def _styles(cls):
        """
        Return styles in a symbol manager style in a dict.

        The dict key consist of
        "fews_filter::fews_location::fews_parameter"
        """
        result = {}
    #    for icon_style in cls.objects.all():
    #        result[icon_style._key] = {
    #            'icon': icon_style.icon,
    #            'mask': (icon_style.mask, ),
    #            'color': icon_style.color.to_tuple()
    #            }
        return result

    @classmethod
    def _lookup(cls):
        """
        Return style lookup dictionary based on class objects.

        This lookup dictionary is cached and it is rebuild every time
        the IconStyle table changes.

        The structure (always) has 3 levels and is used to lookup icon
        styles with fallback in a fast way:

        level 0 (highest) {None: {level1}, "<fews_filter_id>": {level1}, ...}

        level 1 {None: {level2}, "<fews_location_id>": {level2}, ...}

        level 2 {None: icon_key, "<fews_parameter_id>": icon_key, ...}
        """

        lookup = {}

        # Insert style into lookup
        #for style in cls.objects.all():
        #    level0 = style.fews_filter.pk if style.fews_filter else None
        #    level1 = style.fews_location.pk if style.fews_location else None
        #    level2 = (style.fews_parameter.pk
        #              if style.fews_parameter else None)
        #    if level0 not in lookup:
        #        lookup[level0] = {}
        #    if level1 not in lookup[level0]:
        #        lookup[level0][level1] = {}
        #    if level2 not in lookup[level0][level1]:
        #        lookup[level0][level1][level2] = style._key
        #    # Every 'breach' needs a 'None' / default side.
        #    if None not in lookup:
        #        lookup[None] = {}
        #    if None not in lookup[level0]:
        #        lookup[level0][None] = {}
        #    if None not in lookup[level0][level1]:
        #        lookup[level0][level1][None] = '%s::%s::' % (
        #            level0 if level0 else '',
        #            level1 if level1 else '')
        return lookup

    @classmethod
    def _styles_lookup(cls, ignore_cache=False):
        cache_lookup = cache.get(cls.CACHE_KEY)

        if cache_lookup is None or ignore_cache:
            # Calculate styles and lookup and store in cache.
            styles = cls._styles()
            lookup = cls._lookup()
            cache.set(cls.CACHE_KEY, (styles, lookup))
        else:
            # The cache has a 2-tuple (styles, lookup) stored.
            styles, lookup = cache_lookup

        return styles, lookup

    @classmethod
    def style(
        cls,
        fews_filter_pk,
        fews_location_pk, fews_parameter_pk,
        styles=None, lookup=None, ignore_cache=False):
        """
        Return the best corresponding icon style and return in format:

        'xx::yy::zz',
        {'icon': 'icon.png',
         'mask': 'mask.png',
         'color': (1,1,1,0)
         }
        """

        # Hack - removing IconStyle
        return '::::', {
            'icon': 'meetpuntPeil.png',
            'mask': ('meetpuntPeil_mask.png', ),
            'color': (0.0, 0.5, 1.0, 1.0)
            }

        if styles is None or lookup is None:
            styles, lookup = cls._styles_lookup(ignore_cache)

        try:
        #    level1 = lookup.get(fews_filter_pk, lookup[None])
        #    level2 = level1.get(fews_location_pk, level1[None])
        #    found_key = level2.get(fews_parameter_pk, level2[None])
        #    result = styles[found_key]
            pass
        except KeyError:
            # Default, this only occurs when '::::::' is not defined
            return '::::', {
                'icon': 'meetpuntPeil.png',
                'mask': ('meetpuntPeil_mask.png', ),
                'color': (0.0, 0.5, 1.0, 1.0)
                }

        return found_key, result
#
#
# For Django 1.3:
# @receiver(post_save, sender=Setting)
# @receiver(post_delete, sender=Setting)
#def icon_style_post_save_delete(sender, **kwargs):
#    """
#    Invalidates cache after saving or deleting an IconStyle.
#    """
#    logger.debug('Changed IconStyle fewsunblobbed. '
#                 'Invalidating cache for %s...' %
#                 sender.CACHE_KEY)
#    cache.delete(sender.CACHE_KEY)
#
#
#post_save.connect(icon_style_post_save_delete, sender=IconStyle)
#post_delete.connect(icon_style_post_save_delete, sender=IconStyle)
