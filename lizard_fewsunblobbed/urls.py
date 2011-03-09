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
    # url(r'^cache_filters/$',
    #     'lizard_fewsunblobbed.views.cache_filters',
    #     name="fews_cache_filters",
    #     ),
    (r'^map/', include('lizard_map.urls')),
    )


if settings.DEBUG:
    urlpatterns += patterns(
        '',
        (r'', include('staticfiles.urls')),
        (r'^map/', include('lizard_map.urls')),
        (r'^ui/', include('lizard_ui.urls')),
        (r'^admin/', include(admin.site.urls)),
    )
