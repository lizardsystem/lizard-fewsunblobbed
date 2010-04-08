from django.db import models
from composite_pk import composite

class Filter(models.Model):
    fkey = models.IntegerField(primary_key=True)
    id = models.TextField(unique=True) 
    name = models.TextField(blank=True) 
    description = models.TextField(blank=True) 
    issubfilter = models.BooleanField()
    parentfkey = models.ForeignKey('Filter', null=True, blank=True, db_column='parentfkey')
    isendnode = models.BooleanField()

    class Meta:
        db_table = u'filter'

    def __unicode__(self):
        return '%d %s (%s)'%(self.fkey, self.id, self.name)

class Location(models.Model):
    lkey = models.IntegerField(primary_key=True)
    id = models.TextField(unique=True)
    name = models.TextField(blank=True)
    parentid = models.TextField(blank=True)
    description = models.TextField(blank=True)
    shortname = models.TextField(blank=True) 
    tooltiptext = models.TextField(blank=True)
    x = models.FloatField(blank=True)
    y = models.FloatField(blank=True)
    z = models.FloatField(blank=True)
    longitude = models.FloatField(blank=True)
    latitude = models.FloatField(blank=True)    
    class Meta:
        db_table = u'location'

    def __unicode__(self):
        return '%d %s (%s)'%(self.lkey, self.id, self.name)

class Parameter(models.Model):
    pkey = models.IntegerField(primary_key=True)
    id = models.TextField(unique=True)
    name = models.TextField(blank=True)
    shortname = models.TextField(blank=True)
    unit = models.TextField(blank=True)
    parametertype = models.TextField(blank=True)
    parametergroup = models.TextField(blank=True)
    class Meta:
        db_table = u'parameter'

    def __unicode__(self):
        return '%d %s (%s)'%(self.pkey, self.id, self.name)

class Timeserie(models.Model):
    tkey = models.IntegerField(primary_key=True)
    moduleinstanceid = models.TextField(blank=True)
    timestep = models.TextField(blank=True)
    filterkey = models.ForeignKey(Filter, db_column='filterkey')
    locationkey = models.ForeignKey(Location, db_column='locationkey')
    parameterkey = models.ForeignKey(Parameter, db_column='parameterkey')
    class Meta:
        db_table = u'timeserie'

    def __unicode__(self):
        return '%s (%s::%s::%s)'%(self.moduleinstanceid, self.filterkey, self.locationkey, self.parameterkey)

class Timeseriedata(composite.CompositePKModel):
    tkey = models.ForeignKey(Timeserie, primary_key=True, db_column='tkey')
    tsd_time = models.DateTimeField(primary_key=True, db_column='tsd_time')
    tsd_value = models.FloatField(blank=True)
    tsd_flag = models.IntegerField(blank=True)
    tsd_detection = models.BooleanField()
    tsd_comments = models.TextField(blank=True)
    class Meta:
        db_table = u'timeseriedata'

    def __unicode__(self):
        return '%s %s %s'%(self.tkey, self.tsd_time, self.tsd_value)


