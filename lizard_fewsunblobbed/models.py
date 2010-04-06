# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.

from django.db import models
from composite_pk import composite

class Filter(models.Model):
    fkey = models.IntegerField(primary_key=True)
    id = models.TextField(unique=True) # This field type is a guess.
    name = models.TextField(blank=True) # This field type is a guess.
    description = models.TextField(blank=True) # This field type is a guess.
    issubfilter = models.IntegerField(null=True, blank=True)
    parentfkey = models.ForeignKey('Filter', null=True, blank=True, db_column='parentfkey')
    isendnode = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = u'filter'

    def __unicode__(self):
        return '%d %s (%s)'%(self.fkey, self.id, self.name)

class Location(models.Model):
    lkey = models.IntegerField(primary_key=True)
    id = models.TextField(unique=True) # This field type is a guess.
    name = models.TextField(blank=True) # This field type is a guess.
    parentid = models.TextField(blank=True) # This field type is a guess.
    description = models.TextField(blank=True) # This field type is a guess.
    shortname = models.TextField(blank=True) # This field type is a guess.
    tooltiptext = models.TextField(blank=True) # This field type is a guess.
    x = models.TextField(blank=True) # This field type is a guess.
    y = models.TextField(blank=True) # This field type is a guess.
    z = models.TextField(blank=True) # This field type is a guess.
    longitude = models.TextField(blank=True) # This field type is a guess.
    latitude = models.TextField(blank=True) # This field type is a guess.
    class Meta:
        db_table = u'location'

class Parameter(models.Model):
    pkey = models.IntegerField(primary_key=True)
    id = models.TextField(unique=True) # This field type is a guess.
    name = models.TextField(blank=True) # This field type is a guess.
    shortname = models.TextField(blank=True) # This field type is a guess.
    unit = models.TextField(blank=True) # This field type is a guess.
    parametertype = models.TextField(blank=True) # This field type is a guess.
    parametergroup = models.TextField(blank=True) # This field type is a guess.
    class Meta:
        db_table = u'parameter'

class Timeserie(models.Model):
    tkey = models.IntegerField(primary_key=True)
    moduleinstanceid = models.TextField() # This field type is a guess.
    timestep = models.TextField() # This field type is a guess.
    filterkey = models.ForeignKey(Filter)
    locationkey = models.ForeignKey(Location)
    parameterkey = models.ForeignKey(Parameter)
    class Meta:
        db_table = u'timeserie'

class Timeseriedata(composite.CompositePKModel):
    tkey = models.ForeignKey(Timeserie, primary_key=True, db_column='tkey')
    tsd_time = models.TextField(primary_key=True, db_column='tsd_time') # This field type is a guess.
    tsd_value = models.TextField(blank=True) # This field type is a guess.
    tsd_flag = models.TextField(blank=True) # This field type is a guess.
    tsd_detection = models.TextField(blank=True) # This field type is a guess.
    tsd_comments = models.TextField(blank=True) # This field type is a guess.
    class Meta:
        db_table = u'timeseriedata'

