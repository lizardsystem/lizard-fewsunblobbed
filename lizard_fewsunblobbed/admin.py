from django.contrib import admin
from lizard_fewsunblobbed.models import Filter
from lizard_fewsunblobbed.models import Location
from lizard_fewsunblobbed.models import Parameter
from lizard_fewsunblobbed.models import TimeSeriesKey
from lizard_fewsunblobbed.models import TimeSeriesValuesAndFlag
from lizard_fewsunblobbed.models import TimeStep
from lizard_fewsunblobbed.models import FilterTimeSeriesKey

class TimeSeriesValuesAndFlagAdmin(admin.ModelAdmin):
    fields = ['scalarvalue', 'flags', 'datetime']

#class TimeserieAdmin(admin.ModelAdmin):
#    list_display = ['__unicode__', 'data_count', ]
#    list_filter = ('filterkey', 'parameterkey', )
#admin.site.register(Timeserie, TimeserieAdmin)

admin.site.register(Filter)
admin.site.register(Location)
admin.site.register(Parameter)
admin.site.register(TimeSeriesKey)
admin.site.register(TimeSeriesValuesAndFlag, TimeSeriesValuesAndFlagAdmin)
admin.site.register(TimeStep)
admin.site.register(FilterTimeSeriesKey)
