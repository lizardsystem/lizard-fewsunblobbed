from django.contrib import admin
from lizard_fewsunblobbed.models import Filter
from lizard_fewsunblobbed.models import Location
from lizard_fewsunblobbed.models import Parameter
from lizard_fewsunblobbed.models import Timeserie
# from lizard_fewsunblobbed.models import Timeseriedata

# class TimeseriedataAdmin(admin.ModelAdmin):
#     fields = ['tsd_value', 'tsd_flag', 'tsd_detection', 'tsd_comments', ]
'''
class TimeserieAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'data_count', ]
    list_filter = ('filterkey', 'parameterkey', )

admin.site.register(Filter)
admin.site.register(Location)
admin.site.register(Parameter)
admin.site.register(Timeserie, TimeserieAdmin)
'''

# admin.site.register(Timeseriedata, TimeseriedataAdmin)
