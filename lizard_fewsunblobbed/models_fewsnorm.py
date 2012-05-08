# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
import datetime

from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.contrib.gis.geos import GEOSGeometry
from django.db import transaction
from django.contrib.gis.geos import Point
from django.conf import settings

from composite_pk import composite

from lizard_geo.models import GeoObject
from lizard_geo.models import GeoObjectGroup

from lizard_map.coordinates import rd_to_wgs84

from lizard_security.manager import FilteredGeoManager
from lizard_security.models import DataSet

from timeseries import timeseries
from treebeard.al_tree import AL_Node


import logging
logger = logging.getLogger(__name__)


# Note: all fewsnorm dbs are assumed to have this schema.
#SCHEMA_PREFIX = 'nskv00_opdb\".\"'
SCHEMA_PREFIX = 'kvwn00_opdb\".\"'
#SCHEMA_PREFIX = 'kvrl00_opdb\".\"'


class Filter(AL_Node):
    """Fews filter object."""

    # treebeard expects (hardcoded) fields 'id' and 'parent', while
    # fews exposes fkey and parentfkey.
    id = models.IntegerField(primary_key=True, db_column='filterKey'))
    # treebeard requirement (see 'id')
    parent = models.ForeignKey('Filter', null=True, blank=True, db_column='parentFilterKey')
    # since 'id' is already used, we remap 'id' to 'fews_id'.
    fews_id = models.CharField(max_length=64, unique=True, blank=False, db_column='id')
    name = models.CharField(max_length=64, blank=True)
    description = models.CharField(max_length=255, blank=True)
    parentfilterid = models.CharField(max_length=64, db_column='parentFilterId')
    validationiconsvisible = models.IntegerField(null=False, default=0, db_column='validationIconsVisible')
    mapextentid = models.CharField(max_length=64, blank=True, db_column='mapExtentId')
    viewpermission = models.CharField(max_length=64, blank=True, db_column='viewPermission')
    editpermission = models.CharField(max_length=64, blank=True, db_column='editPermission')
    node_order_by = ['name']

    class Meta:
        verbose_name = "Filter"
        verbose_name_plural = "Filters"
        db_table = u'Filters'
        managed = False

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
        engine = settings.DATABASES['default']['ENGINE']
        return engine.split('.')[-1]


class Users(models.Model):
    userkey = models.IntegerField(primary_key=True, db_column='userKey')
    id = models.CharField(unique=True, null=False, max_length=64)
    name = models.CharField(max_length=64, blank=True)

    class Meta:
        #db_table = SCHEMA_PREFIX + u'users'
        managed = False

    def __unicode__(self):
        return u'%s' % self.id


class ParameterGroups(models.Model):
    groupkey = models.IntegerField(primary_key=True, db_column='groupKey')
    id = models.CharField(unique=True, blank=False, max_length=64)
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=64)
    parametertype = models.CharField(max_length=64, null=False, db_column='parameterType')
    unit = models.CharField(max_length=64)
    displayunit = models.CharField(max_length=64, db_column='displayUnit')

    class Meta:
        #db_table = SCHEMA_PREFIX + u'parametergroups'
        managed = False

    def __unicode__(self):
        return u'%s' % self.id


class Location(models.Model):
    """
    Fewsnorm Location.
    """
    locationkey = models.IntegerField(primary_key=True, db_column='locationKey')
    id = models.CharField(unique=True, blank=False, max_length=64)
    name = models.CharField(max_length=64)
    shortname = models.CharField(max_length=64, db_column='shortName')
    description = models.CharField(max_length=255)
    icon = models.CharField(max_length=64)
    tooltip = models.CharField(max_length=64, db_column='toolTip')
    parentlocationid = models.CharField(max_length=64, db_column='parentLocationId')
    visibilitystarttime = models.DateTimeField(db_column='visibilityStartTime')
    visibilityendtime = models.DateTimeField(db_column='visibilityEndTime')
    x = models.FloatField()
    y = models.FloatField()
    z = models.FloatField()
    area = models.FloatField()
    related_location = models.CharField(max_length=64, null=True, blank=True)

    class Meta:
        #db_table = u'locations'
        managed = False

    def __unicode__(self):
        return u'%s' % self.id

    @classmethod
    def from_raw(cls, schema_prefix='', related_location='id', ident=None):
        """Due to schema difficulties and performance, use this function.

        if you provide an id, that id will be selected

        if you provide related_location, that column will be returned
        as well.
        """
        raw_query = """
SELECT locationkey, id, name, shortname, description, icon, tooltip, parentlocationid,
       parentlocationid, visibilitystarttime, visibilityendtime, x, y, z, area, %(related_location)s as related_location
FROM
       "%(schema_prefix)s"."locations"
""" % {'schema_prefix': schema_prefix, 'related_location': related_location}
        if ident is not None:
            raw_query += " WHERE id='%s'" % ident
        return cls.objects.raw(raw_query)


# TODO: flexible schema_prefix
# def getParameterModel(schema_prefix=None):

#     class ParameterMetaclass(models.base.ModelBase):
#         def __new__(cls, name, bases, attrs):
#             name += schema_prefix
#             return models.base.ModelBase.__new__(cls, name, bases, attrs)


class Parameter(models.Model):
    parameterkey = models.IntegerField(primary_key=True, db_column='parameterKey')
    groupkey = models.ForeignKey(ParameterGroups, db_column='groupKey')
    id = models.CharField(max_length=64, unique=True, blank=False)
    name = models.CharField(max_length=64)
    shortname = models.CharField(max_length=64, db_column='shortName')
    description = models.CharField(max_length=255)
    valueresolution = models.FloatField(db_column='valueResolution')
    allowmissing = models.CharField(max_length=128, db_column='allowMissing')
    standardname = models.CharField(max_length=64, db_column='standardName')
    standardnamemodifier = models.CharField(max_length=64, db_column='standardNameModifier')
    attributea = models.CharField(max_length=64)
    attributeb = models.FloatField()

    class Meta:
        #db_table = SCHEMA_PREFIX + u'parameters'
        managed = False

    def __unicode__(self):
        return '%s' % self.id

    @classmethod
    def from_raw(cls, schema_prefix=''):
        """Due to schema difficulties and performance, use this function"""
        return cls.objects.raw("""
SELECT par.parameterkey as parameterkey, gr.id as groupkey,
       par.id as id, par.name as name, par.shortname as shortname,
       par.description as description, par.valueresolution as valueresolution,
       par.attributea as attributea, par.attributeb as attributeb
FROM
       "%(schema_prefix)s"."parameters" as par
INNER JOIN "%(schema_prefix)s"."parametergroups" as gr ON (par.groupkey = gr.groupkey)
""" % {'schema_prefix': schema_prefix})


# class Qualifiers(models.Model):
#     qualifierkey = models.IntegerField(primary_key=True,
#                                        db_column='qualifierkey')
#     id = models.CharField(unique=True, max_length=64)
#     description = models.CharField(max_length=64)

#     class Meta:
#         #db_table = SCHEMA_PREFIX + u'qualifiers'
#         managed = False

#     def __unicode__(self):
#         return u'%s' % self.id


class QualifierSets(models.Model):
    qualifiersetkey = models.IntegerField(primary_key=True, db_column='qualifierSetKey')
    id = models.CharField(unique=True, blank=False, max_length=64)
    qualifierid1 = models.CharField(max_length=64)
    qualifierid2 = models.CharField(max_length=64)
    qualifierid3 = models.CharField(max_length=64)
    qualifierid4 = models.CharField(max_length=64)

    class Meta:
        # db_table = SCHEMA_PREFIX + u'qualifiersets'
        managed = False

    def __unicode__(self):
        return u'%s' % self.id

    @classmethod
    def from_raw(cls, schema_prefix=''):
        """Due to schema difficulties and performance, use this function
        """
        return cls.objects.raw("""
SELECT
    qs.qualifierSetKey as qualifierSetKey,
    qs.id as id,
    q1.id as qualifierid1,
    q2.id as qualifierid2,
    q3.id as qualifierid3,
    q4.id as qualifierid4
FROM
    "%(schema_prefix)s"."QualifierSets" as qs
LEFT OUTER JOIN
    "%(schema_prefix)s"."Qualifiers" as q1 ON (qs.qualifierKey1 = q1.qualifierKey)
LEFT OUTER JOIN
    "%(schema_prefix)s"."Qualifiers" as q2 ON (qs.qualifierKey2 = q2.qualifierKey)
LEFT OUTER JOIN
    "%(schema_prefix)s"."Qualifiers" as q3 ON (qs.qualifierKey3 = q3.qualifierKey)
LEFT OUTER JOIN
    "%(schema_prefix)s"."Qualifiers" as q4 ON (qs.qualifierKey4 = q4.qualifierKey)
""" % {'schema_prefix': schema_prefix})


class ModuleInstances(models.Model):
    moduleinstancekey = models.IntegerField(primary_key=True,
                                            db_column='moduleinstancekey')
    id = models.CharField(unique=True, max_length=64)
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=64)

    class Meta:
        # db_table = SCHEMA_PREFIX + u'moduleinstances'
        managed = False

    def __unicode__(self):
        return u'%s' % self.id

    @classmethod
    def from_raw(cls, schema_prefix=''):
        """Due to schema difficulties and performance, use this function
        """
        return cls.objects.raw("""
SELECT moduleinstancekey, id, name, description
FROM
       "%(schema_prefix)s"."moduleinstances"
""" % {'schema_prefix': schema_prefix})


class Timesteps(models.Model):
    timestepkey = models.IntegerField(primary_key=True, db_column='timeStepKey')
    id = models.CharField(unique=True, null=False, max_length=64)
    label = models.CharField(max_length=64)  # on fewsnorm-dev
    #description = models.CharField(max_length=64)  # on testdatabase

    class Meta:
        #db_table = SCHEMA_PREFIX + u'timesteps'
        managed = False

    def __unicode__(self):
        return u'%s' % self.id

    @classmethod
    def from_raw(cls, schema_prefix=''):
        """Due to schema difficulties and performance, use this function
        """
        return cls.objects.raw("""
SELECT timestepkey, id, label
FROM
       "%(schema_prefix)s"."timesteps"
""" % {'schema_prefix': schema_prefix})


# class AggregationPeriods(models.Model):
#     aggregationperiodkey = models.IntegerField(
#         primary_key=True,
#         db_column='aggregationperiodkey')
#     id = models.CharField(unique=True, max_length=64)
#     description = models.CharField(max_length=64)

#     class Meta:
#         #db_table = SCHEMA_PREFIX + u'aggregationperiods'
#         managed = False

#     def __unicode__(self):
#         return u'%s' % self.id


class TimeSeriesKeys(models.Model):
    """
    Due to difficulties in different schemas and databases:

    Use from_raw.
    """
    serieskey = models.IntegerField(primary_key=True, db_column='seriesKey')
    locationkey = models.CharField(max_length=64)
    parameter = models.CharField(max_length=64)
    unit = models.CharField(max_length=64)
    qualifierset = models.CharField(max_length=64, blank=True, null=True)
    moduleinstance = models.CharField(max_length=64, blank=True, null=True)
    timestep = models.CharField(max_length=64, blank=True, null=True)
    aggregationperiod = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        #db_table = SCHEMA_PREFIX + u'timeserieskeys'
        managed = False

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

    @classmethod
    def from_raw(cls, schema_prefix='', params={}):
        """
        Return series objects as described in this model.

        Provide params to filter results.

        Params may have the following keys:
        - location: locations.id
        - parameter: parameters.id
        - moduleinstance: moduleinstances.id
        - timestep: timesteps.id
        - qualifierset: qualifiersets.id
        """
        raw_query = """
SELECT serieskey,
       loc.id as location,
       par.id as parameter,
       pgr.unit as unit,
       qua.id as qualifierset,
       mod.id as moduleinstance,
       tst.id as timestep ,
       agg.id as aggregationperiod
FROM
       "%(schema_prefix)s"."timeserieskeys" as ts
INNER JOIN "%(schema_prefix)s"."locations" as loc ON (ts.locationkey = loc.locationkey)
INNER JOIN "%(schema_prefix)s"."parameters" as par ON (ts.parameterkey = par.parameterkey)
LEFT OUTER JOIN "%(schema_prefix)s"."qualifiersets" as qua ON (ts.qualifiersetkey = qua.qualifiersetkey)
INNER JOIN "%(schema_prefix)s"."moduleinstances" as mod ON (ts.moduleinstancekey = mod.moduleinstancekey)
INNER JOIN "%(schema_prefix)s"."timesteps" as tst ON (ts.timestepkey = tst.timestepkey)
LEFT OUTER JOIN "%(schema_prefix)s"."aggregationperiods" as agg ON (ts.aggregationperiodkey = agg.aggregationperiodkey)
INNER JOIN "%(schema_prefix)s"."parametergroups" as pgr ON (par.groupkey = pgr.groupkey)
""" % {'schema_prefix': schema_prefix}
        if params:
            db_fields = {'location': 'loc.id',
                         'parameter': 'par.id',
                         'moduleinstance': 'mod.id',
                         'timestep': 'tst.id',
                         'qualifierset': 'qua.id'}
            raw_query += 'WHERE ' + ' AND '.join([
                    "%s = '%s'" % (db_fields[a], b) for a, b in params.items()])
        return cls.objects.raw(raw_query)


class Event(models.Model):
    """
    A single event.

    Use from_raw to get events.
    """
    # series = models.ForeignKey(Series,
    #                            primary_key=True,
    #                            db_column='serieskey')
    timestamp = models.DateTimeField(db_column='datetime')
    value = models.FloatField(db_column='scalarvalue')
    flag = models.IntegerField(db_column='flags')
    comment = models.CharField(max_length=64)

    class Meta:
        #db_table = SCHEMA_PREFIX + u'timeseriesvaluesandflags'
        managed = False

    def __unicode__(self):
        return u'%s value=%s %s' % (
            self.timestamp,
            self.value,
            self.flag)

    @classmethod
    def filter_latest_before_deadline(
        cls, series_set, deadline, schema_prefix=''):
        """filter events matching series_set

        `series_set` is a QuerySet holding Series.

        `deadline` is a time threshold: we only consider the events
        before `deadline` and per Series we return the latest one.
        """

        ## get the concrete database from one of the locations in the
        ## series set.

        # assume the serie_set is not empty!
        first_serie = series_set[0]
        location = GeoLocationCache.objects.get(ident=first_serie.location)
        db_name = location.fews_norm_source.database_name
        schema_prefix = location.fews_norm_source.database_schema_name

        series_set__pk = ','.join(tuple(str(s.pk) for s in series_set))
        deadline__iso = deadline.isoformat()

        ## execute the query.
        raw_query = """\
SELECT
  e.datetime as id, e.datetime as timestamp, e.scalarvalue as value,
  e.flags as flag, c.comment as comment
FROM \"%(schema_prefix)s\".\"timeseriesvaluesandflags\" e
  JOIN (SELECT serieskey, max(datetime) AS datetime
        FROM \"%(schema_prefix)s\".\"timeseriesvaluesandflags\"
        WHERE serieskey in (%(serieskey)s)
          AND datetime < '%(deadline)s'
              GROUP BY serieskey) latest
  ON e.serieskey = latest.serieskey
  AND e.datetime = latest.datetime
LEFT OUTER JOIN "%(schema_prefix)s"."timeseriescomments" as c
  ON (c.datetime = e.datetime AND c.serieskey = e.serieskey)
""" % {
                'schema_prefix': schema_prefix,
                'serieskey': series_set__pk,
                'deadline': deadline__iso}
        return cls.objects.raw(raw_query).using(db_name)

    @classmethod
    def from_raw(cls, series, dt_start=None, dt_end=None,
                 with_comments=False, schema_prefix=''):
        """
        Get events (with comments) from fewsnorm.
        """
        # We add a fake id, because the Django RawQuerySet requires it.
        raw_query = """
SELECT e.datetime as id, e.datetime as timestamp, e.scalarvalue as value, e.flags as flag, c.comment as comment
FROM "%(schema_prefix)s"."timeseriesvaluesandflags" as e
LEFT OUTER JOIN "%(schema_prefix)s"."timeseriescomments" as c ON (c.datetime = e.datetime AND c.serieskey = e.serieskey)
""" % {'schema_prefix': schema_prefix}

        expressions = ['e.serieskey = %s' % series.serieskey]
        if dt_start:
            expressions.append("e.datetime >= '%s'" % dt_start.isoformat())
        if dt_end:
            expressions.append("e.datetime <= '%s'" % dt_end.isoformat())
        raw_query += 'WHERE ' + ' AND '.join(expressions)

        return cls.objects.raw(raw_query)

    @classmethod
    def agg_from_raw(cls, series, dt_start=None, dt_end=None, schema_prefix='',
                     agg_function='avg', agg_period='year'):
        """
        Same as from_raw, but aggregates.

        Aggregate by
        Function: avg, sum
        Period: year, month, day

        PostgreSQL aggregating sql:

        select date_part('year', datetime) as year, date_part('month',
        datetime) as month, sum(scalarvalue) from
        nskv00_opdb.timeseriesvaluesandflags group by year, month
        order by year, month;

        Yes, the raw queries are very ugly.
        """
        agg_functions = set(['avg', 'sum'])
        agg_periods = set(['year', 'quarter', 'month', 'day'])

        if agg_function not in agg_functions:
            raise Exception('Series.agg_from_raw: agg_function %s not in %s' % (
                    agg_function, agg_functions))
        if agg_period not in agg_periods:
            raise Exception('Series.agg_from_raw: agg_period %s not in %s' % (
                    agg_period, agg_periods))

        expressions = ['e.serieskey = %s' % series.serieskey]
        if dt_start:
            expressions.append("e.datetime >= '%s'" % dt_start.isoformat())
        if dt_end:
            expressions.append("e.datetime <= '%s'" % dt_end.isoformat())
        where_clause = 'WHERE ' + ' AND '.join(expressions)

        if agg_period == 'year':
            raw_query = """
SELECT
       date_part('year', datetime) as id,
       date_part('year', datetime) as year,
       to_timestamp(to_char(date_part('year', datetime), 'FM9999') || ' 01 01', 'YYYY MM DD') as timestamp,
       %(agg_function)s(scalarvalue) as value,
       '' as comment,
       max(e.flags) as flag
FROM
        "%(schema_prefix)s"."timeseriesvaluesandflags" as e
%(where_clause)s
GROUP BY year
ORDER BY year;
""" % {'agg_function': agg_function, 'schema_prefix': schema_prefix, 'where_clause': where_clause}
        elif agg_period == 'quarter':
            raw_query = """
SELECT
       date_part('year', datetime) as id,
       date_part('year', datetime) as year,
       trunc((date_part('month', datetime) - 1) / 3) * 3 + 1 as month,
       to_timestamp(to_char(date_part('year', datetime), 'FM9999') || ' ' || to_char(trunc((date_part('month', datetime) - 1) / 3) * 3 + 1, 'FM99') || ' 01', 'YYYY MM DD') as timestamp,
       %(agg_function)s(scalarvalue) as value,
       '' as comment,
       max(e.flags) as flag
FROM
        "%(schema_prefix)s"."timeseriesvaluesandflags" as e
%(where_clause)s
GROUP BY year, month
ORDER BY year, month;
""" % {'agg_function': agg_function, 'schema_prefix': schema_prefix, 'where_clause': where_clause}
        elif agg_period == 'month':
            raw_query = """
SELECT
       date_part('year', datetime) as id,
       date_part('year', datetime) as year,
       date_part('month', datetime) as month,
       to_timestamp(to_char(date_part('year', datetime), 'FM9999') || ' ' || to_char(date_part('month', datetime), 'FM99') || ' 01', 'YYYY MM DD') as timestamp,
       %(agg_function)s(scalarvalue) as value,
       '' as comment,
       max(e.flags) as flag
FROM
        "%(schema_prefix)s"."timeseriesvaluesandflags" as e
%(where_clause)s
GROUP BY year, month
ORDER BY year, month;
""" % {'agg_function': agg_function, 'schema_prefix': schema_prefix, 'where_clause': where_clause}
        elif agg_period == 'day':
            raw_query = """
SELECT
       date_part('year', datetime) as id,
       date_part('year', datetime) as year,
       date_part('month', datetime) as month,
       date_part('day', datetime) as day,
       to_timestamp(to_char(date_part('year', datetime), 'FM9999') || ' ' || to_char(date_part('month', datetime), 'FM99') || ' ' || to_char(date_part('day', datetime), 'FM99'), 'YYYY MM DD') as timestamp,
       %(agg_function)s(scalarvalue) as value,
       '' as comment,
       max(e.flags) as flag
FROM
        "%(schema_prefix)s"."timeseriesvaluesandflags" as e
%(where_clause)s
GROUP BY year, month, day
ORDER BY year, month, day;
""" % {'agg_function': agg_function, 'schema_prefix': schema_prefix, 'where_clause': where_clause}

        return cls.objects.raw(raw_query)

    @classmethod
    def time_series(cls, source, multi_series, dt_start=None, dt_end=None):
        """
        Retrieve events from time series.

        Result is timeseries objects in a dict (loc_id, par_id).
        """
        result = {}
        for single_series in multi_series:
            # Fill new timeseries with events from dt_start to dt_end
            events = Event.from_raw(
                single_series, dt_start, dt_end,
                schema_prefix=source.database_schema_name).using(
                source.database_name)

            # Put the events in a Timeseries object
            new_timeseries = timeseries.TimeSeries()
            new_timeseries.location_id = single_series.location
            new_timeseries.parameter_id = single_series.parameter
            new_timeseries.time_step = single_series.timestep
            new_timeseries.units = single_series.unit
            for event in events:
                new_timeseries[event.timestamp] = (
                    event.value, event.flag, event.comment)

            result[single_series.location,
                   single_series.parameter,
                   single_series.unit] = new_timeseries
        return result


# class TimeseriesManualEditsHistory(models.Model):
#     serieskey = models.ForeignKey(Series,
#                                   primary_key=True,
#                                   db_column='serieskey')
#     editdatetime = models.DateTimeField(primary_key=True)
#     datetime = models.DateTimeField()
#     userkey = models.ForeignKey(Users, db_column='userkey',
#                                 blank=True, null=True)
#     scalarvalue = models.FloatField()
#     flags = models.IntegerField()
#     comments = models.CharField(max_length=64)

#     class Meta:
#         db_table = SCHEMA_PREFIX + u'timeseriesmanualeditshistory'
#         managed = False

#     def __unicode__(self):
#         return u'%s %s' % (self.serieskey, self.datetime)


# Managed models that are in the default database.

class QualifierSetCacheManager(models.Manager):
    def get_by_natural_key(self, ident):
        return self.get(ident=ident)


class QualifierSetCache(models.Model):
    objects = QualifierSetCacheManager()

    ident = models.CharField(max_length=64)

    class Meta:
        ordering = ('ident', )

    def __unicode__(self):
        return '%s' % self.ident

    def natural_key(self):
        return (self.ident, )


class ParameterCacheManager(models.Manager):
    def get_by_natural_key(self, ident):
        return self.get(ident=ident)


class ParameterCache(models.Model):
    objects = ParameterCacheManager()

    ident = models.CharField(max_length=64)

    name = models.CharField(max_length=64, null=True, blank=True)

    shortname = models.CharField(max_length=64, null=True, blank=True)

    class Meta:
        ordering = ('ident', )

    def __unicode__(self):
        return '%s' % self.ident

    def api_url(self):
        return reverse('lizard_fewsnorm_api_parameter_detail',
                       kwargs={'ident': self.ident})

    def natural_key(self):
        return (self.ident, )


class ModuleCacheManager(models.Manager):
    def get_by_natural_key(self, ident):
        return self.get(ident=ident)


class ModuleCache(models.Model):
    objects = ModuleCacheManager()

    ident = models.CharField(max_length=64)

    class Meta:
        ordering = ('ident', )

    def __unicode__(self):
        return u'%s' % self.ident

    def natural_key(self):
        return (self.ident, )


class TimeStepCacheManager(models.Manager):
    def get_by_natural_key(self, ident):
        return self.get(ident=ident)


class TimeStepCache(models.Model):
    objects = TimeStepCacheManager()

    ident = models.CharField(max_length=64)

    class Meta:
        ordering = ('ident', )

    def __unicode__(self):
        return u'%s' % self.ident

    def natural_key(self):
        return (self.ident, )


class GeoLocationCacheManager(FilteredGeoManager):
    def get_by_natural_key(self, ident):
        # Normally we would use self.get, but that doesn't work in
        # this case.
        return GeoLocationCache.objects.get(ident=ident)


class GeoLocationCache(GeoObject):
    """
    Geo cache for locations from all data sources.
    """
    objects = GeoLocationCacheManager()

    data_set = models.ForeignKey(DataSet, null=True, blank=True)
    fews_norm_source = models.ForeignKey('FewsNormSource')
    name = models.CharField(max_length=64)
    shortname = models.CharField(max_length=64)
    icon = models.CharField(max_length=64)
    tooltip = models.CharField(max_length=64)
    parameter = models.ManyToManyField(
        ParameterCache, null=True, blank=True, through='TimeSeriesCache')
    module = models.ManyToManyField(
        ModuleCache, null=True, blank=True, through='TimeSeriesCache')
    timestep = models.ManyToManyField(
        TimeStepCache, null=True, blank=True, through='TimeSeriesCache')
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ('ident', 'name')

    def __unicode__(self):
        try:
            return '%s (%s)' % (self.ident, self.fews_norm_source)
        except:
            # You can use GeoLocationCache as a memory object without
            # defining fews_norm_source.
            return '%s' % self.ident

    def api_url(self):
        return reverse('lizard_fewsnorm_api_location_detail',
                       kwargs={'ident': self.ident})

    def natural_key(self):
        return (self.ident, )


class TimeSeriesCache(models.Model):
    """
    Cache time series objects from all sources.

    Use this object as an entrypoint to fetch data.
    """
    geolocationcache = models.ForeignKey(GeoLocationCache)
    parametercache = models.ForeignKey(ParameterCache)
    modulecache = models.ForeignKey(ModuleCache)
    timestepcache = models.ForeignKey(TimeStepCache)
    qualifiersetcache = models.ForeignKey(QualifierSetCache,
                                          blank=True, null=True)
    active = models.BooleanField(default=True)

    # class Meta:
    #     unique_together = ('geolocationcache', 'parametercache',
    #                        'modulecache', 'timestepcache')

    def __unicode__(self):
        return '%s,%s,%s' % (
            self.geolocationcache.ident,
            self.parametercache.ident,
            self.id)

    def hash(self):
        if self.qualifiersetcache is not None:
            qualifier_set_id = self.qualifiersetcache.id
        else:
            qualifier_set_id = None
        return '%s::%s::%s::%s::%s' % (
            self.geolocationcache.ident, self.parametercache.ident,
            self.modulecache.ident, self.timestepcache.ident, qualifier_set_id)

    def api_url(self):
        return reverse('lizard_fewsnorm_api_timeseries_detail',
                       kwargs={'id': self.id})

    def _series_set(self):
        """
        Return django QuerySet of Series.
        """
        params = {
            'location': self.geolocationcache.ident,
            'parameter': self.parametercache.ident,
            'moduleinstance': self.modulecache.ident,
            'timestep': self.timestepcache.ident
            }
        if self.qualifiersetcache:
            params['qualifierset'] = self.qualifiersetcache.ident
        source = self.geolocationcache.fews_norm_source
        return Series.from_raw(
            schema_prefix=source.database_schema_name,
            params=params).using(source.database_name)

    def get_latest_event(self, now=None, with_comments=False):
        """
        Return latest event for this timeseries.

        The with_comments option is here for backwards
        compatibility. Comments are always returned.
        """
        if now is None:
            now = datetime.datetime.now()
        series = self._series_set()
        event = Event.filter_latest_before_deadline(
            series, now)[0]
        return event

    def get_timeseries(self, dt_start=None, dt_end=None):
        """
        Return TimeSeries dictionary.

        Key is (location, parameter, unit), Value is TimeSeries object.
        """
        source = self.geolocationcache.fews_norm_source
        series_set = self._series_set()
        return Event.time_series(source, series_set, dt_start, dt_end)

    @classmethod
    def save_raw_dict(cls, timeseries):
        """
        Use this to save a batch of timeseries.

        Timeseries are stored as dictionaries as when using .values() function.

        You must add an attribute 'new' to each timeseries to
        determine create or update.
        """
        from django.db import connection, transaction
        cursor = connection.cursor()

        no_saved = 0
        no_created = 0
        no_existing = 0
        no_nonactive = 0

        for single_timeseries in timeseries:
            if not single_timeseries['active']:
                no_nonactive += 1
            if not single_timeseries.get('changed', True):
                # We do not have to save this object.
                continue
            timeseries_dict = {
                'id': single_timeseries.get('id', None),  # Id only for existing items
                'geo_id': single_timeseries['geolocationcache__id'],
                'par_id': single_timeseries['parametercache__id'],
                'mod_id': single_timeseries['modulecache__id'],
                'tst_id': single_timeseries['timestepcache__id'],
                'active': 'TRUE' if single_timeseries['active'] else 'FALSE',
                'qua_id': single_timeseries['qualifiersetcache__id'] if
                single_timeseries['qualifiersetcache__id'] else 'null',  # Can be None
                }
            if single_timeseries['new']:
                #insert
                cursor.execute("""
INSERT INTO lizard_fewsnorm_timeseriescache (geolocationcache_id, parametercache_id, modulecache_id, timestepcache_id, active, qualifiersetcache_id) VALUES (%(geo_id)d, %(par_id)d, %(mod_id)d, %(tst_id)d, %(active)s, %(qua_id)s)
""" % timeseries_dict)
                no_created += 1
            else:
                cursor.execute("""
UPDATE lizard_fewsnorm_timeseriescache SET geolocationcache_id = %(geo_id)d, parametercache_id = %(par_id)d, modulecache_id = %(mod_id)d, timestepcache_id = %(tst_id)d, active = %(active)s, qualifiersetcache_id = %(qua_id)s WHERE id = %(id)d
""" % timeseries_dict)
                no_existing += 1

            no_saved += 1
            if no_saved % 10000 == 0:
                logger.debug('Saved %d objects.' % no_saved)
        logger.debug('committing...')
        transaction.commit_unless_managed()

        return no_saved, no_created, no_existing, no_nonactive


class TrackRecordCache(GeoObject):
    """
    Hold results from complex query on fewsnorm database
    """
    objects = FilteredGeoManager()

    data_set = models.ForeignKey(DataSet, null=True, blank=True)
    fews_norm_source = models.ForeignKey('FewsNormSource')

    parameter = models.ForeignKey(ParameterCache, null=True, blank=True)
    location = models.ForeignKey(GeoLocationCache, null=True, blank=True)
    module = models.ForeignKey(ModuleCache, null=True, blank=True)

    datetime = models.DateTimeField()
    value = models.FloatField()

    class Meta:
        ordering = ['datetime']

    def __unicode__(self):
        return '%s - %s' % (self.location, self.parameter)


class FewsNormSource(models.Model):
    """
    Define a source database for fews norm.

    We're using fewsnorm database models:
    - Location
    - Parameter
    - ModuleInstances
    - Timesteps
    - QualifierSets
    - Series
    """
    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)
    database_name = models.CharField(max_length=40, unique=True)
    database_schema_name = models.CharField(
        max_length=80, null=True, blank=True)
    active = models.BooleanField(default=True)

    def source_locations(self):
        return list(Location.from_raw(
            schema_prefix=self.database_schema_name).using(self.database_name))

    @transaction.commit_on_success
    def get_or_create_geoobjectgroup(self, user_name=None):
        if user_name is None:
            user_obj = User.objects.all()[0]  # Random user
        else:
            user_obj = User.objects.get(username=user_name)
        group_name = 'FEWSNORM::%s' % self.database_name
        group_slug = slugify(group_name)
        geo_object_group, created = GeoObjectGroup.objects.get_or_create(
            slug=group_slug,
            defaults={'name': group_name, 'created_by': user_obj})
        if not created:
            geo_object_group.name = group_name
            geo_object_group.created_by = user_obj
            geo_object_group.save()
        if created:
            logger.info('Newly created geoobjectgroup %s' % geo_object_group)
            geo_object_group.source_log = 'FEWSNORM::%s' % self.database_name
            geo_object_group.save()
        return geo_object_group

    @transaction.commit_on_success
    def sync_parameter_cache(self):
        """
        Fill ParameterCache
        """
        parameters = {}
        no_touched = 0
        no_created = 0
        for parameter in Parameter.from_raw(
            self.database_schema_name).using(self.database_name):

            parameter_cache, created = ParameterCache.objects.get_or_create(
                ident=parameter.id,
                defaults={
                    'name': parameter.name,
                    'shortname': parameter.shortname,
                }
            )
            if created:
                logger.info('Newly created parameter %s' % parameter_cache)
                no_created += 1
            else:
                parameter_cache.name = parameter.name
                parameter_cache.shortname = parameter.shortname
                parameter_cache.save()
                # logger.debug('Updated/touched parameter %s' % parameter_cache)
                no_touched += 1
            parameters[parameter_cache.ident] = parameter_cache
        logger.info('No of parameters created: %d' % no_created)
        logger.info('No of parameters updated/touched: %d' % no_touched)
        return parameters

    @transaction.commit_on_success
    def sync_module_cache(self):
        """
        Fill ModuleCache.
        """
        modules = {}
        for module in ModuleInstances.from_raw(
            self.database_schema_name).using(self.database_name):

            module_cache, _ = ModuleCache.objects.get_or_create(
                ident=module.id)
            modules[module_cache.ident] = module_cache
        return modules

    @transaction.commit_on_success
    def sync_time_step_cache(self):
        """
        Fill TimeStepCache.
        """
        time_steps = {}
        for time_step in Timesteps.from_raw(
            self.database_schema_name).using(self.database_name):

            time_step_cache, _ = TimeStepCache.objects.get_or_create(
                ident=time_step.id)
            time_steps[time_step_cache.ident] = time_step_cache
        return time_steps

    @transaction.commit_on_success
    def sync_qualifier_set_cache(self):
        """
        Fill QualifierSetCache
        """
        qualifier_sets = {}
        for qualifier_set in QualifierSets.from_raw(
            self.database_schema_name).using(
            self.database_name):

            qualifier_set_cache, cr = QualifierSetCache.objects.get_or_create(
                ident=qualifier_set.id)
            qualifier_sets[qualifier_set_cache.ident] = qualifier_set_cache
            if cr:
                logger.info('Newly created qualifier set %s' %
                            qualifier_set_cache)
        return qualifier_sets

    @transaction.commit_on_success
    def sync_location_cache(
        self, data_set=None, user_name=None):
        """
        Fill GeoLocationCache.

        Inactivates all existing entries, then re-enable all
        occurrences that are present in the source.

        parameters and modules are dicts with ParameterCache and
        ModuleCache. Keys are their idents.
        """
        logger.debug('Reading existing locations from source...')
        source_locations = self.source_locations()
        geo_object_group = self.get_or_create_geoobjectgroup(user_name)

        logger.debug('Reading current locations cache...')
        locations = {}
        for glc in GeoLocationCache.objects.filter(fews_norm_source=self):
            # glc.active = False
            glc.changed = False  # For saving
            glc.visited = False  # For saving
            locations[glc.ident] = glc

        no_existing = 0
        no_created = 0
        no_nonactive = 0
        logger.debug('Checking %d locations...' % len(source_locations))
        for location in source_locations:
            new_ident = location.id[:80]
            wgs84_x, wgs84_y = rd_to_wgs84(location.x, location.y)
            geom = GEOSGeometry(Point(wgs84_x, wgs84_y), srid=4326)
            new_location = False
            if new_ident in locations:
                # Update existing
                no_existing += 1
                current_location = locations[new_ident]

                # Detect changes for saving
                if current_location.data_set != data_set:
                    current_location.changed = True
                if current_location.fews_norm_source != self:
                    current_location.changed = True
                if current_location.name != location.name:
                    current_location.changed = True
                if current_location.shortname != location.shortname:
                    current_location.changed = True
                if current_location.icon != '%s' % location.icon:
                    current_location.changed = True
                if current_location.tooltip != '%s' % location.tooltip:
                    current_location.changed = True
                if current_location.geo_object_group != geo_object_group:
                    current_location.changed = True
                if current_location.geometry != geom:
                    current_location.changed = True
                if current_location.changed:
                    logger.debug('Changed location: %s' % current_location)
            else:
                # New
                no_created += 1
                current_location = GeoLocationCache(ident=new_ident)
                current_location.changed = True
                new_location = True  # For logging

            # (Over)write params

            current_location.visited = True  # For saving

            current_location.data_set = data_set
            current_location.fews_norm_source = self
            current_location.name = '%s' % location.name
            current_location.shortname = '%s' % location.shortname
            current_location.icon = '%s' % location.icon
            current_location.tooltip = '%s' % location.tooltip
            current_location.geo_object_group = geo_object_group
            current_location.geometry = geom
            current_location.active = True
            if new_location:
                logger.debug('New location: %s' % current_location)

            locations[new_ident] = current_location

        # Save locations
        logger.debug('Saving...')
        no_saved = 0
        for location in locations.values():
            if not location.visited:
                location.active = False
                no_nonactive += 1
                logger.warning('Inactive location: %s' % location)
                no_saved += 1
                location.save()
            if location.visited and location.changed:
                no_saved += 1
                location.save()

        logger.info('Newly created locations: %d' % no_created)
        logger.info('Non-active locations: %d' % no_nonactive)
        logger.info('Saved locations: %d' % no_saved)
        return locations

    @transaction.commit_on_success
    def sync_time_series_cache(
        self, locations, parameters, modules, time_steps,
        qualifier_sets, data_set_name=None):
        """
        Synchronize the time series cache with the source.

        Inactivates all existing entries, then re-enable all
        occurrences that are present in the source.

        Note that active timeseries CAN refer to an inactive location.
        """
        def ts_hash(ts_dict):
            """Generate temp hash for a timeseries dict"""
            return '%s::%s::%s::%s::%s' % (
                ts_dict['geolocationcache__ident'],
                ts_dict['parametercache__ident'],
                ts_dict['modulecache__ident'],
                ts_dict['timestepcache__ident'],
                ts_dict.get('qualifiersetcache__ident', None))

        # Collect new series
        logger.debug('Reading existing series from source...')
        series = list(Series.from_raw(self.database_schema_name).using(
            self.database_name))

        # Read current cache
        logger.debug('Reading existing series cache...')
        time_series_cache_dict = {}
        for single_time_series_cache in TimeSeriesCache.objects.filter(
            geolocationcache__fews_norm_source=self).values(
            'geolocationcache__ident', 'geolocationcache__id',
            'parametercache__ident', 'parametercache__id',
            'modulecache__ident', 'modulecache__id',
            'timestepcache__ident', 'timestepcache__id',
            'qualifiersetcache__ident', 'qualifiersetcache__id',
            'id'):
            # The idents are only needed to create the temporary
            # hash. When creating a new object, it is sufficient to
            # use an id only.

            single_time_series_cache['visited'] = False  # Custom
            single_time_series_cache['changed'] = False  # Custom, for TimeSeriesCache.save_raw
            single_time_series_cache['new'] = False  # Custom, for TimeSeriesCache.save_raw
            time_series_cache_dict[
                ts_hash(single_time_series_cache)] = single_time_series_cache

        no_processed = 0
        logger.debug('Checking %d series...' % len(series))
        for single_series in series:
            series_hash = single_series.hash()
            no_processed += 1
            if series_hash in time_series_cache_dict:
                # Update existing
                current_time_series = time_series_cache_dict[series_hash]
                # Check if essential attributes have changed
                if single_series.location != current_time_series['geolocationcache__ident']:
                    current_time_series['changed'] = True
                    # Ident is for consistency, it is not saved.
                    current_time_series['geolocationcache__ident'] = single_series.location
                    current_time_series['geolocationcache__id'] = locations[single_series.location].id
                if single_series.parameter != current_time_series['parametercache__ident']:
                    current_time_series['changed'] = True
                    # Ident is for consistency, it is not saved.
                    current_time_series['parametercache__ident'] = single_series.parameter
                    current_time_series['parametercache__id'] = parameters[single_series.parameter].id
                if single_series.moduleinstance != current_time_series['modulecache__ident']:
                    current_time_series['changed'] = True
                    # Ident is for consistency, it is not saved.
                    current_time_series['modulecache__ident'] = single_series.moduleinstance
                    current_time_series['modulecache__id'] = modules[single_series.moduleinstance].id
                if single_series.timestep != current_time_series['timestepcache__ident']:
                    current_time_series['changed'] = True
                    # Ident is for consistency, it is not saved.
                    current_time_series['timestepcache__ident'] = single_series.timestep
                    current_time_series['timestepcache__id'] = time_steps[single_series.timestep].id
                if single_series.qualifierset != current_time_series['qualifiersetcache__ident']:
                    current_time_series['changed'] = True
                    # Ident is for consistency, it is not saved.
                    if single_series.qualifierset:
                        qualifier_set_id = qualifier_sets[single_series.qualifierset].id
                    else:
                        qualifier_set_id = None
                    current_time_series['qualifiersetcache__ident'] = single_series.qualifierset
                    current_time_series['qualifiersetcache__id'] = qualifiers_set_id
            else:
                # New
                if single_series.qualifierset:
                    qualifier_set_id = qualifier_sets[single_series.qualifierset].id
                else:
                    qualifier_set_id = None
                current_time_series = {
                    'geolocationcache__id': locations[single_series.location].id,
                    'parametercache__id': parameters[single_series.parameter].id,
                    'modulecache__id': modules[single_series.moduleinstance].id,
                    'timestepcache__id': time_steps[single_series.timestep].id,
                    'qualifiersetcache__id': qualifier_set_id,
                    'changed': True
                    }
                current_time_series['new'] = True  # For TimeSeriesCache.save_raw
            current_time_series['active'] = True
            current_time_series['visited'] = True
            time_series_cache_dict[series_hash] = current_time_series
            # if no_processed % 100000 == 0:
            #     logger.debug('# processed timeseries: %d' % no_processed)

        # Look for non-active time series
        for ts_dict in time_series_cache_dict.values():
            if not ts_dict['visited']:
                ts_dict['active'] = False
                ts_dict['changed'] = True

        no_saved, no_created, no_existing, no_nonactive = TimeSeriesCache.save_raw_dict(
            time_series_cache_dict.values())

        logger.info('Saved timeseries: %d' % no_saved)
        logger.info('Newly created timeseries: %d' % no_created)
        logger.info('Updated existing timeseries: %d' % no_existing)
        logger.info('Non-active timeseries: %d' % no_nonactive)

    # @transaction.commit_on_success
    def sync_track_record_cache(self, data_set=None):
        """
        Synchronize trackrecords

        TODO: DOES NOT WORK ANYMORE
        """
        TRACKRECORD_PARAMETERS = ('BodemP.kritisch', )
        TRACKRECORD_COORDINATES = ('Xpos', 'Ypos')
        TRACKRECORD_GEOOBJECTGROUP = 'TrackRecordCache'

        # Get the first superuser for the geoobject group
        geo_object_group_user = User.objects.filter(is_superuser=True)[0]

        geo_object_group = GeoObjectGroup.objects.get_or_create(
            name=TRACKRECORD_GEOOBJECTGROUP,
            slug=slugify(TRACKRECORD_GEOOBJECTGROUP),
            defaults = {'created_by': geo_object_group_user}
        )[0]

        parametercaches = [ParameterCache.objects.get(ident=trp)
                           for trp in TRACKRECORD_PARAMETERS]
        xpos_cache, ypos_cache = [ParameterCache.objects.get(ident=trp)
                                  for trp in TRACKRECORD_COORDINATES]

        for p in parametercaches:
            geolocationcaches = GeoLocationCache.objects.filter(parameter=p)

            for g in geolocationcaches:
                # Collect value, xpos and ypos events at this location
                value_series = Series.from_raw(
                    schema_prefix=self.database_schema_name,
                    params={'location': g.ident,
                            'parameter': p.ident}
                ).using(self.database_name)
                value_events = Event.from_raw(
                    value_series[0],
                    schema_prefix=self.database_schema_name
                ).using(self.database_name)
                xpos_series = TimeSeriesCache.objects.get(
                    geolocationcache=g,
                    parametercache=xpos_cache,
                )
                xpos_events = Event.from_raw(
                    value_series,
                    schema_prefix=self.database_schema_name
                ).using(self.database_name)
                ypos_series = TimeSeriesCache.objects.get(
                    geolocationcache=g,
                    parametercache=ypos_cache,
                )
                ypos_events = Event.from_raw(
                    value_series,
                    schema_prefix=self.database_schema_name
                ).using(self.database_name)

                # Some dicts for easy matching of events by date
                xpos_events_dict = dict([(str(e[0]), e)
                                          for e in xpos_events])
                ypos_events_dict = dict([(str(e[0]), e)
                                          for e in ypos_events])

                for value_event in value_events:
                    # Note we check if coordinates are present for a value,
                    # but not if values are present for each coordinate.
                    datestr = str(value_event[0])
                    if (datestr in xpos_events_dict and
                        datestr in ypos_events_dict):
                        x_rd = xpos_events_dict[datestr][1][0]
                        y_rd = ypos_events_dict[datestr][1][0]
                        x_wgs84, y_wgs84 = rd_to_wgs84(x_rd, y_rd)
                        geometry = GEOSGeometry(
                            Point(x_wgs84, y_wgs84),
                            srid=4326,
                        )

                        track_record_cache_kwargs = {
                            'data_set': data_set,
                            'fews_norm_source': self,
                            'parameter': p,
                            'location': g,
                            'module': None,
                            'geo_object_group': geo_object_group,
                            'geometry': geometry,
                            'datetime': value_event[0],
                            'value': value_event[1][0],
                        }
                        TrackRecordCache.objects.get_or_create(
                            **track_record_cache_kwargs)
        return None

    def __unicode__(self):
        return '%s' % (self.name)

    def api_url(self):
        return reverse(
            'lizard_fewsnorm_api_adapter',
            kwargs={'fews_norm_source_slug': self.slug})
