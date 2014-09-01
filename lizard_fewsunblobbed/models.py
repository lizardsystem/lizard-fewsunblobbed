# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from functools import partial
import hashlib
import logging

from django import db
from django.conf import settings
from django.core import serializers
from django.core.cache import cache
from django.core.cache import get_cache
from django.db import models
from lizard_map import coordinates
from treebeard.al_tree import AL_Node
import django.db.models.options as options

logger = logging.getLogger(__name__)

# allows a custom attribute in the model Meta class
options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('is_fews_model',)

TSK_HAS_DATA_CACHE_KEY = 'lizard_fewsunblobbed.models.timeserieskey_hasdata'
PARAMETER_CACHE_KEY = 'lizard_fewsunblobbed.models.parameter_cache_key::%s'
RELATED_FILTERS_CACHE_KEY = 'lizard_fewsunblobbed.models.filter.related::%s'

FEWS_MANAGED = False
if hasattr(settings, 'FEWS_MANAGED'):
    FEWS_MANAGED = settings.FEWS_MANAGED

Nullable64CharField = partial(models.CharField, max_length=64, null=True, blank=True)


class Filter(AL_Node):
    """Fews filter object."""
    # treebeard expects (hardcoded) fields 'id' and 'parent', while
    # fews exposes id and parentFilterId.
    id                     = models.IntegerField(primary_key=True, db_column='filterKey')
    parent                 = models.ForeignKey('Filter', null=True, blank=True, db_column='parentFilterId', related_name='+', to_field='fews_id')
    # since 'id' is already used, we remap 'id' to 'fews_id'.
    fews_id                = models.CharField(max_length=64, unique=True, null=False, blank=False, db_column='id')
    name                   = Nullable64CharField()
    #description            = models.CharField(max_length=255, null=True, blank=True)
    #validationiconsvisible = models.IntegerField(null=False, default=0, db_column='validationIconsVisible')
    mapextentid            = Nullable64CharField(db_column='mapExtentId')
    viewpermission         = Nullable64CharField(db_column='viewPermission')
    #editpermission         = Nullable64CharField(db_column='editPermission')
    node_order_by = ['name']

    class Meta:
        verbose_name = "Filter"
        verbose_name_plural = "Filters"
        db_table = u'Filters'
        is_fews_model = True
        managed = FEWS_MANAGED

    def __unicode__(self):
        return u'%s (id=%s)' % (self.name, self.fews_id)

    __isendnode = None
    @property
    def isendnode(self):
        if self.__isendnode is None:
            self.__isendnode = not Filter.objects.filter(parent=self).exists()
        return self.__isendnode

    __issubfilter = None
    @property
    def issubfilter(self):
        if self.__issubfilter is None:
            self.__issubfilter = self.parent is None
        return self.__issubfilter

    @property
    def has_parameters(self):
        """Return whether there is at least one connected timeserie.

        Note: parameters of descendants are not counted."""
        return query_parameters_exist_for_filter(self)

    def parameters(self, ignore_cache=False):
        """Return parameters for this filter and the filters children.

        The parameters returned have an added property 'filterkey'.
        """
        parameter_cache_key = PARAMETER_CACHE_KEY % str(self.id)
        fs_cache = get_cache('unblobbed_cache')
        parameters = fs_cache.get(parameter_cache_key)
        if parameters is None or ignore_cache:
            parameters = []  # Start new one
            # Fetch all filter -> parameter combinations.
            for f in [self] + self.get_descendants():
                for p in query_distinct_parameters_for_filter(f):

                    # Add filterkey for use in template (it's a m2m).
                    p.filterkey = f
                    if f != self:
                        p.name = '%s (%s)' % (p.name, f.name)
                    parameters.append(p)

            # parameters = param_dict.values()
            parameters.sort(key=lambda p: p.name)
            fs_cache.set(parameter_cache_key, parameters, 8 * 60 * 60)

        return parameters

    @classmethod
    def get_database_engine(cls):
        """Overriding treebeard: it grabs the 'default' database engine."""
        engine = settings.DATABASES['fewsnorm']['ENGINE']
        return engine.split('.')[-1]

    @classmethod
    def dump_bulk(cls, parent=None, keep_ids=True):
        '''Dumps a tree branch to a python data structure.
        NOTE: Bugfix for sib_order already in treebeard 1.61.
        Overridden from treebeard to retain has_parameters, isendnode.
        Also uses 'fews_id' to build the parent->child relations, unlike treebeard.
        '''
        serializable_cls = cls._get_serializable_model()
        if parent and serializable_cls != cls and \
                parent.__class__ != serializable_cls:
            parent = serializable_cls.objects.get(pk=parent.pk)

        # a list of nodes: not really a queryset, but it works
        objs = serializable_cls.get_tree(parent)

        ret, lnk = [], {}
        for node, pyobj in zip(objs, serializers.serialize('python', objs)):
            depth = node.get_depth()
            # django's serializer stores the attributes in 'fields'
            fields = pyobj['fields']
            del fields['parent']

            # non-sorted trees have this
            if 'sib_order' in fields:
                del fields['sib_order']

            if 'id' in fields:
                del fields['id']

            fields['has_parameters'] = node.has_parameters
            fields['isendnode'] = node.isendnode
            newobj = {'data': fields}
            if keep_ids:
                newobj['id'] = pyobj['pk']

            if (not parent and depth == 1) or \
                    (parent and depth == parent.get_depth()):
                # at a leaf
                ret.append(newobj)
            else:
                parentobj = lnk[node.parent.fews_id]
                if 'children' not in parentobj:
                    parentobj['children'] = []
                parentobj['children'].append(newobj)
            lnk[node.fews_id] = newobj
        return ret

    @classmethod
    def get_related_filters_for(cls, filterkey, ignore_cache=False):
        node = cls.objects.get(pk=filterkey)
        cache_key = RELATED_FILTERS_CACHE_KEY % str(node)
        cache_key = hashlib.sha256(cache_key).hexdigest()
        # ^^^ Make sure there are no spaces in the cache key.
        fs_cache = get_cache('unblobbed_cache')
        related_filters = fs_cache.get(cache_key)
        if related_filters is None or ignore_cache:
            related_filters = set([node.pk])
            #while node.parent != None:
            #    node = node.parent
            #    if node.pk in related_filters:
            #        # pk already in set, so circular parent->child reference
            #        raise Exception("circular relation for filters %s" % node)
            #    related_filters.add(node.pk)
            for childnode in node.get_descendants():
                related_filters.add(childnode.pk)
            fs_cache.set(cache_key, related_filters, 8 * 60 * 60)
        return related_filters

class ParameterGroup(models.Model):
    groupkey      = models.IntegerField(primary_key=True, db_column='groupKey')
    id            = models.CharField(unique=True, null=False, blank=False, max_length=64)
    name          = models.CharField(max_length=64)
    #description   = models.CharField(max_length=255)
    #parametertype = models.CharField(max_length=64, null=False, blank=False, db_column='parameterType')
    unit          = models.CharField(max_length=64)
    displayunit   = models.CharField(max_length=64, db_column='displayUnit')

    class Meta:
        verbose_name = "ParameterGroup"
        verbose_name_plural = "ParameterGroups"
        db_table = u'ParameterGroups'
        is_fews_model = True
        managed = FEWS_MANAGED

    def __unicode__(self):
        return u'%s' % self.id


class Parameter(models.Model):
    parameterkey         = models.IntegerField(primary_key=True, db_column='parameterKey')
    group                = models.ForeignKey('ParameterGroup', null=False, db_column='groupKey')
    id                   = models.CharField(max_length=64, unique=True, null=False, blank=False)
    name                 = models.CharField(max_length=64)
    shortname            = models.CharField(max_length=64, db_column='shortName')
    #description          = models.CharField(max_length=255)
    valueresolution      = models.FloatField(db_column='valueResolution')
    #allowmissing         = models.IntegerField(null=False, default=0, db_column='allowMissing')
    #standardname         = models.CharField(max_length=128, db_column='standardName')
    #standardnamemodifier = models.CharField(max_length=64, db_column='standardNameModifier')
    #attributea           = models.CharField(max_length=64, db_column='attributeA')
    #attributeb           = models.FloatField(db_column='attributeB')

    class Meta:
        verbose_name = "Parameter"
        verbose_name_plural = "Parameters"
        db_table = u'Parameters'
        is_fews_model = True
        managed = FEWS_MANAGED

    def __unicode__(self):
        return '%s' % self.id


class TimeStep(models.Model):
    timestepkey = models.IntegerField(primary_key=True, db_column='timeStepKey')
    id          = models.CharField(unique=True, null=False, max_length=64)
    label       = models.CharField(max_length=64)

    class Meta:
        verbose_name = "TimeStep"
        verbose_name_plural = "TimeSteps"
        db_table = u'Timesteps'
        is_fews_model = True
        managed = FEWS_MANAGED

    def __unicode__(self):
        return u'%s' % self.id


class Location(models.Model):
    """
    Fewsnorm Location.
    """
    locationkey         = models.IntegerField(primary_key=True, db_column='locationKey')
    id                  = models.CharField(unique=True, null=False, blank=False, max_length=64)
    name                = models.CharField(max_length=64)
    #shortname           = models.CharField(max_length=64, db_column='shortName')
    description         = models.CharField(max_length=255)
    icon                = models.CharField(max_length=64)
    tooltip             = models.CharField(max_length=64, db_column='toolTip')
    parentlocationid    = models.CharField(max_length=64, db_column='parentLocationId')
    #visibilitystarttime = models.DateTimeField(db_column='visibilityStartTime')
    #visibilityendtime   = models.DateTimeField(db_column='visibilityEndTime')
    x                   = models.FloatField(null=False)
    y                   = models.FloatField(null=False)
    #z                   = models.FloatField()
    #area                = models.FloatField()
    #relationalocationid = models.CharField(max_length=64, db_column='relationALocationId')
    #relationblocationid = models.CharField(max_length=64, db_column='relationBLocationId')
    #attributea          = models.CharField(max_length=64, db_column='attributeA')
    #attributeb          = models.FloatField(db_column='attributeB')

    class Meta:
        verbose_name = "Location"
        verbose_name_plural = "Locations"
        db_table = u'Locations'
        is_fews_model = True
        managed = FEWS_MANAGED

    def __unicode__(self):
        return u'%s' % self.id

    def google_coords(self):
        return coordinates.rd_to_google(self.x, self.y)

    def wgs84_coords(self):
        return coordinates.rd_to_wgs84(self.x, self.y)

class ModuleInstance(models.Model):
    moduleinstancekey = models.IntegerField(primary_key=True, db_column='moduleInstanceKey')
    id                = models.CharField(null=False, unique=True, max_length=64)
    name              = models.CharField(max_length=64)
    description       = models.CharField(max_length=255)

    class Meta:
        verbose_name = "ModuleInstance"
        verbose_name_plural = "ModuleInstances"
        db_table = u'ModuleInstances'
        is_fews_model = True
        managed = FEWS_MANAGED

    def __unicode__(self):
        return u'%s' % self.id


class AggregationPeriod(models.Model):
    aggregationperiodkey = models.IntegerField(primary_key=True, db_column='aggregationPeriodKey')
    id                   = models.CharField(null=False, unique=True, max_length=64)
    description          = models.CharField(max_length=255)

    class Meta:
        verbose_name = "AggregationPeriod"
        verbose_name_plural = "AggregationPeriods"
        db_table = u'AggregationPeriods'
        is_fews_model = True
        managed = FEWS_MANAGED

    def __unicode__(self):
        return u'%s' % self.id


class Qualifier(models.Model):
    qualifierkey = models.IntegerField(primary_key=True, db_column='qualifierKey')
    id           = models.CharField(null=False, unique=True, max_length=64)
    #name         = models.CharField(max_length=64)
    #shortname    = models.CharField(max_length=64, db_column='shortName')
    description  = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Qualifier"
        verbose_name_plural = "Qualifiers"
        db_table = u'Qualifiers'
        is_fews_model = True
        managed = FEWS_MANAGED

    def __unicode__(self):
        return u'%s' % self.id


class QualifierSet(models.Model):
    qualifiersetkey = models.IntegerField(primary_key=True, db_column='qualifierSetKey')
    id              = models.CharField(unique=True, null=False, blank=False, max_length=64)
    qualifier1      = models.ForeignKey('Qualifier', null=False, db_column='qualifierKey1', related_name='+')
    qualifier2      = models.ForeignKey('Qualifier', null=True, db_column='qualifierKey2', related_name='+')
    qualifier3      = models.ForeignKey('Qualifier', null=True, db_column='qualifierKey3', related_name='+')
    qualifier4      = models.ForeignKey('Qualifier', null=True, db_column='qualifierKey4', related_name='+')

    class Meta:
        verbose_name = "QualifierSet"
        verbose_name_plural = "QualifierSets"
        db_table = u'QualifierSets'
        is_fews_model = True
        managed = FEWS_MANAGED

    def __unicode__(self):
        return u'%s' % self.id


class TimeSeriesKey(models.Model):
    series            = models.IntegerField(primary_key=True, db_column='seriesKey')
    location          = models.ForeignKey('Location', null=False, db_column='locationKey')
    parameter         = models.ForeignKey('Parameter', null=False, db_column='parameterKey')
    qualifierset      = models.ForeignKey('QualifierSet', null=True, db_column='qualifierSetKey')
    moduleinstance    = models.ForeignKey('ModuleInstance', null=False, db_column='moduleInstanceKey')
    timestep          = models.ForeignKey('TimeStep', null=False, db_column='timeStepKey')
    aggregationperiod = models.ForeignKey('AggregationPeriod', null=True, db_column='aggregationPeriodKey')
    #valuetype         = models.IntegerField(null=False, default=0, db_column='valueType')
    #modificationtime  = models.DateTimeField(db_column='modificationTime')

    class Meta:
        verbose_name = "TimeSeriesKey"
        verbose_name_plural = "TimeSeriesKeys"
        db_table = u'TimeSeriesKeys'
        is_fews_model = True
        managed = FEWS_MANAGED

    def hash(self):
        return '%s::%s::%s::%s::%s' % (
            self.location, self.parameter, self.moduleinstance,
            self.timestep, self.qualifierset)

    def __unicode__(self):
        return u'%s %s %s %s' % (
            self.location,
            self.parameter,
            self.qualifierset,
            self.moduleinstance)

    @property
    def name(self):
        """Return name for use in graph legends"""
        return u'%s (%s): %s' % (self.parameter.name,
                                self.parameter.group.unit,
                                self.location.name)

    @property
    def shortname(self):
        """Return name for use in graph legends"""
        return u'%s' % (self.location.name)

    @classmethod
    def has_data_dict(cls, ignore_cache=False):
        """
        Return for each timeserie id if it has data.

        If a timeserie has data, its id is listed in the returned
        dict. Handy when looping over great amounts of timeseries.
        """
        cache_key = TSK_HAS_DATA_CACHE_KEY
        fs_cache = get_cache('unblobbed_cache')
        result = fs_cache.get(cache_key)
        if result is None or ignore_cache:
            logger.info('Populating TimeSeriesKey.has_data_dict...')
            tsd = TimeSeriesValuesAndFlag.objects.all().values('series').distinct()
            tsd_dict = {}
            for row in tsd:
                tsd_dict[row['series']] = None  # Just make an entry
            logger.debug('... populating with %s items', len(tsd_dict))
            fs_cache.set(cache_key, tsd_dict, 8 * 60 * 60)
            result = tsd_dict
        return result


class TimeSeriesValuesAndFlag(models.Model):
    #id = models.IntegerField(primary_key=True, db_column='id') # TODO: NOTE: not in FEWSNORM-ZZL
    series = models.ForeignKey('TimeSeriesKey', db_column='seriesKey')
    datetime = models.DateTimeField(db_column='dateTime')
    scalarvalue = models.FloatField(db_column='scalarValue', null=True)
    flags = models.IntegerField(db_column='flags', null=False)

    class Meta:
        unique_together = ['series', 'datetime']
        verbose_name = "TimeSeriesValuesAndFlag"
        verbose_name_plural = "TimeSeriesValuesAndFlags"
        db_table = u'TimeSeriesValuesAndFlags'
        is_fews_model = True
        managed = FEWS_MANAGED

    def __unicode__(self):
        return u'%s value=%s %s' % (
            self.datetime,
            self.scalarvalue,
            self.flags)


class FilterTimeSeriesKey(models.Model):
    filter = models.ForeignKey('Filter', null=False, db_column='filterKey')
    series = models.ForeignKey('TimeSeriesKey', null=False, db_column='seriesKey')

    class Meta:
        verbose_name = "FilterTimeSeriesKey"
        verbose_name_plural = "FilterTimeSeriesKeys"
        db_table = u'FilterTimeSeriesKeys'
        is_fews_model = True
        managed = FEWS_MANAGED


# queries defined here, to make an improvised data access layer,
# and because we expect the need for raw sql optimisations

def query_distinct_parameters_for_filter(filter):
    return Parameter.objects.filter(timeserieskey__filtertimeserieskey__filter=filter).distinct()


def query_parameters_exist_for_filter(filter):
    cache_key = 'unblobbed_filters_with_timeseriessssssss'
    filters_with_timeseries = cache.get(cache_key)
    if filters_with_timeseries is None:
        filters_with_timeseries = FilterTimeSeriesKey.objects.all().values_list(
            'filter', flat=True).distinct()
        cache.set(cache_key, filters_with_timeseries, 8 * 60 * 60)
    return filter.id in filters_with_timeseries


def query_locations_for_filter(filterkey):
    #Location.objects.filter(timeserie__filterkey=self.filterkey)])
    related_filters = Filter.get_related_filters_for(filterkey)
    return Location.objects.filter(timeserieskey__filtertimeserieskey__filter__in=related_filters)


def query_timeseries_for_parameter(filterkey, parameterkey):
    #Timeserie.objects.filter(filterkey=self.filterkey, parameterkey=self.parameterkey)
    related_filters = Filter.get_related_filters_for(filterkey)
    return TimeSeriesKey.objects.filter(filtertimeserieskey__filter__in=related_filters, parameter=parameterkey)


def query_timeseries_for_location(filterkey, parameterkey, locationkey):
    #Timeserie.objects.filter(filterkey=filterkey, locationkey=locationkey, parameterkey=parameterkey)
    related_filters = Filter.get_related_filters_for(filterkey)
    return TimeSeriesKey.objects.filter(filtertimeserieskey__filter__in=related_filters, parameter=parameterkey, location=locationkey)


def query_timeseriedata_for_timeserie(timeserie, start_date, end_date):
    cursor = db.connections['fewsnorm'].cursor()
    q = '''
        SELECT
            "TIMESERIESVALUESANDFLAGS"."DATETIME", "TIMESERIESVALUESANDFLAGS"."SCALARVALUE"
        FROM
            "TIMESERIESVALUESANDFLAGS"
        WHERE
            "TIMESERIESVALUESANDFLAGS"."SERIESKEY" = %s
        AND
            "TIMESERIESVALUESANDFLAGS"."DATETIME" BETWEEN %s and %s
        ORDER BY
            "TIMESERIESVALUESANDFLAGS"."DATETIME" ASC
    '''
    cursor.execute(q, [timeserie.series, start_date, end_date])
    result = cursor.fetchall()
    return result
