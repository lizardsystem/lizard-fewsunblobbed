# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    depends_on = (
        ("lizard_security", "0002_auto__add_usergroup__add_permissionmapper__add_dataset"),
    )

    def forwards(self, orm):


        # Adding field 'Filter.data_set'
        db.add_column(u'filter', 'data_set',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_security.DataSet'], null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Filter.data_set'
        db.delete_column(u'filter', 'data_set_id')


    models = {
        'lizard_fewsunblobbed.filter': {
            'Meta': {'object_name': 'Filter', 'db_table': "u'filter'"},
            'data_set': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_security.DataSet']", 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'fews_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64', 'db_column': "'id'"}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True', 'db_column': "'fkey'"}),
            'isendnode': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'issubfilter': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_fewsunblobbed.Filter']", 'null': 'True', 'db_column': "'parentfkey'", 'blank': 'True'})
        },
        'lizard_fewsunblobbed.location': {
            'Meta': {'object_name': 'Location', 'db_table': "u'location'"},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'latitude': ('django.db.models.fields.FloatField', [], {'blank': 'True'}),
            'lkey': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'longitude': ('django.db.models.fields.FloatField', [], {'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'parentid': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'shortname': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'tooltiptext': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'x': ('django.db.models.fields.FloatField', [], {'blank': 'True'}),
            'y': ('django.db.models.fields.FloatField', [], {'blank': 'True'}),
            'z': ('django.db.models.fields.FloatField', [], {'blank': 'True'})
        },
        'lizard_fewsunblobbed.parameter': {
            'Meta': {'object_name': 'Parameter', 'db_table': "u'parameter'"},
            'id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'parametergroup': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'parametertype': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'pkey': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'shortname': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'unit': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'})
        },
        'lizard_fewsunblobbed.timeserie': {
            'Meta': {'object_name': 'Timeserie', 'db_table': "u'timeserie'"},
            'filterkey': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_fewsunblobbed.Filter']", 'db_column': "'filterkey'"}),
            'locationkey': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_fewsunblobbed.Location']", 'db_column': "'locationkey'"}),
            'moduleinstanceid': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'parameterkey': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_fewsunblobbed.Parameter']", 'db_column': "'parameterkey'"}),
            'timestep': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'tkey': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'})
        },
        'lizard_fewsunblobbed.timeseriedata': {
            'Meta': {'unique_together': "(('tkey', 'tsd_time'),)", 'object_name': 'Timeseriedata', 'db_table': "u'timeseriedata'"},
            'tkey': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'timeseriedata'", 'db_column': "'tkey'", 'to': "orm['lizard_fewsunblobbed.Timeserie']"}),
            'tsd_comments': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'tsd_detection': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'tsd_flag': ('django.db.models.fields.IntegerField', [], {'blank': 'True'}),
            'tsd_time': ('django.db.models.fields.DateTimeField', [], {'primary_key': True, 'db_column': "'tsd_time'"}),
            'tsd_value': ('django.db.models.fields.FloatField', [], {'blank': 'True'})
        },
        'lizard_security.dataset': {
            'Meta': {'ordering': "['name']", 'object_name': 'DataSet'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'})
        }
    }

    complete_apps = ['lizard_fewsunblobbed']
