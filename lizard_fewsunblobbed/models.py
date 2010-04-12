from django.core import serializers
from django.db import models
from composite_pk import composite
from treebeard.al_tree import AL_Node


class Filter(AL_Node):
    # use 'id' and not fkey as treebeard needs this name (is hardcoded)
    id  = models.IntegerField(primary_key=True, db_column='fkey')
    # since 'id' is already used us another name
    fews_id = models.TextField(unique=True, db_column='id')
    name = models.TextField(blank=True)
    description = models.TextField(blank=True)
    issubfilter = models.BooleanField()
    # use 'parent' and not parentfkey as treebeard needs this name (is hardcoded)
    parent = models.ForeignKey('Filter', null=True, blank=True,
                               db_column='parentfkey')
    isendnode = models.BooleanField()
    node_order_by = ['name',]

    class Meta:
        db_table = u'filter'

    def __unicode__(self):
        return '%s (id=%s)' % (self.name, self.fews_id)

    # This method is overriden from the class AL_Node in al_tree.py
    # from the django-treebeard application
    # The method fixes checks first if the field sib_order exist before deleting,
    # which the original version doesn't do (which causes a bug).
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

            newobj = {'data': fields}
            if keep_ids:
                newobj['id'] = pyobj['pk']

            if (not parent and depth == 1) or \
                    (parent and depth == parent.get_depth()):
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
        return '%s (lkey=%s)' % (self.name, self.lkey)


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
        return '%s (pkey=%s)' % (self.name, self.pkey)


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
        return '%s for %s (tkey=%s)' % (self.moduleinstanceid,
                                        self.locationkey.name,
                                        self.tkey)


class Timeseriedata(composite.CompositePKModel):
    tkey = models.ForeignKey(Timeserie,
                             primary_key=True,
                             db_column='tkey',
                             related_name='timeseriedata')
    # ^^^ TODO: this is mighty slow in the django admin.  It grabs all the
    # timeserie names/ids.
    tsd_time = models.DateTimeField(primary_key=True, db_column='tsd_time')
    tsd_value = models.FloatField(blank=True)
    tsd_flag = models.IntegerField(blank=True)
    tsd_detection = models.BooleanField()
    tsd_comments = models.TextField(blank=True)

    class Meta:
        db_table = u'timeseriedata'

    def __unicode__(self):
        return 'Data for %s: %s = %s' % (self.tkey, self.tsd_time, self.tsd_value)
