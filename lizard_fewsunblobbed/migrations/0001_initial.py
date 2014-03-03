# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Filter'
        db.create_table(u'filter', (
            ('id', self.gf('django.db.models.fields.IntegerField')(primary_key=True, db_column='fkey')),
            ('fews_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64, db_column='id')),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('issubfilter', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_fewsunblobbed.Filter'], null=True, db_column='parentfkey', blank=True)),
            ('isendnode', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('lizard_fewsunblobbed', ['Filter'])

        # Adding model 'Location'
        db.create_table(u'location', (
            ('lkey', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('parentid', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('shortname', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('tooltiptext', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
            ('x', self.gf('django.db.models.fields.FloatField')(blank=True)),
            ('y', self.gf('django.db.models.fields.FloatField')(blank=True)),
            ('z', self.gf('django.db.models.fields.FloatField')(blank=True)),
            ('longitude', self.gf('django.db.models.fields.FloatField')(blank=True)),
            ('latitude', self.gf('django.db.models.fields.FloatField')(blank=True)),
        ))
        db.send_create_signal('lizard_fewsunblobbed', ['Location'])

        # Adding model 'Parameter'
        db.create_table(u'parameter', (
            ('pkey', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('shortname', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('unit', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('parametertype', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('parametergroup', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
        ))
        db.send_create_signal('lizard_fewsunblobbed', ['Parameter'])

        # Adding model 'Timeserie'
        db.create_table(u'timeserie', (
            ('tkey', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('moduleinstanceid', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('timestep', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('filterkey', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_fewsunblobbed.Filter'], db_column='filterkey')),
            ('locationkey', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_fewsunblobbed.Location'], db_column='locationkey')),
            ('parameterkey', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_fewsunblobbed.Parameter'], db_column='parameterkey')),
        ))
        db.send_create_signal('lizard_fewsunblobbed', ['Timeserie'])

        # Adding model 'Timeseriedata'
        db.create_table(u'timeseriedata', (
            ('tkey', self.gf('django.db.models.fields.related.ForeignKey')(related_name='timeseriedata', db_column='tkey', to=orm['lizard_fewsunblobbed.Timeserie'])),
            ('tsd_time', self.gf('django.db.models.fields.DateTimeField')(primary_key=True, db_column='tsd_time')),
            ('tsd_value', self.gf('django.db.models.fields.FloatField')(blank=True)),
            ('tsd_flag', self.gf('django.db.models.fields.IntegerField')(blank=True)),
            ('tsd_detection', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('tsd_comments', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
        ))
        db.send_create_signal('lizard_fewsunblobbed', ['Timeseriedata'])

        # Adding unique constraint on 'Timeseriedata', fields ['tkey', 'tsd_time']
        db.create_unique(u'timeseriedata', ['tkey', 'tsd_time'])


    def backwards(self, orm):
        # Removing unique constraint on 'Timeseriedata', fields ['tkey', 'tsd_time']
        db.delete_unique(u'timeseriedata', ['tkey', 'tsd_time'])

        # Deleting model 'Filter'
        db.delete_table(u'filter')

        # Deleting model 'Location'
        db.delete_table(u'location')

        # Deleting model 'Parameter'
        db.delete_table(u'parameter')

        # Deleting model 'Timeserie'
        db.delete_table(u'timeserie')

        # Deleting model 'Timeseriedata'
        db.delete_table(u'timeseriedata')


    models = {
        'lizard_fewsunblobbed.filter': {
            'Meta': {'object_name': 'Filter', 'db_table': "u'filter'"},
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
        }
    }

    complete_apps = ['lizard_fewsunblobbed']