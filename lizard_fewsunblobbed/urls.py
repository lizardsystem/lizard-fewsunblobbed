from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$',
        'lizard_fewsunblobbed.views.fews_browser',
        name="fews_browser",
        ),
    # Graph for fews points
    (r'^timeserie-graph/$',
     'lizard_fewsunblobbed.views.timeserie_graph',
     {},
     "lizard_fewsunblobbed.timeserie_graph"),
    (r'^timeserie-graph/(?P<id>\d*)/$',
     'lizard_fewsunblobbed.views.timeserie_graph',
     {},
     "lizard_fewsunblobbed.timeserie_graph"),
    )


if settings.DEBUG:
    urlpatterns += patterns(
        '',
        (r'', include('staticfiles.urls')),
        (r'^map/', include('lizard_map.urls')),
        (r'^ui/', include('lizard_ui.urls')),
        (r'^admin/', include(admin.site.urls)),
    )
