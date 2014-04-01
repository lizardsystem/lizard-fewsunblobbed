from django.contrib import admin
from lizard_security.admin import SecurityFilteredAdmin

from lizard_fewsunblobbed.models import Filter
from lizard_fewsunblobbed.models import Location
from lizard_fewsunblobbed.models import Parameter
from lizard_fewsunblobbed.models import Timeserie


class FilterAdmin(SecurityFilteredAdmin):
    list_display = ['__unicode__', 'fews_id', 'data_set']


class TimeserieAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'data_count', ]
    list_filter = ('filterkey', 'parameterkey', )


admin.site.register(Filter, FilterAdmin)
admin.site.register(Location)
admin.site.register(Parameter)
admin.site.register(Timeserie, TimeserieAdmin)
