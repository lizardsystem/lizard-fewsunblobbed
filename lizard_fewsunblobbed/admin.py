from django.contrib import admin
from lizard_fewsunblobbed.models import Filter, Location, Parameter, Timeserie, Timeseriedata

class TimeseriedataAdmin(admin.ModelAdmin):
    fields = ['tsd_value', 'tsd_flag', 'tsd_detection', 'tsd_comments', ]

class TimeserieAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'data_count', ]

admin.site.register(Filter)
admin.site.register(Location)
admin.site.register(Parameter)
admin.site.register(Timeserie, TimeserieAdmin)
admin.site.register(Timeseriedata, TimeseriedataAdmin)
