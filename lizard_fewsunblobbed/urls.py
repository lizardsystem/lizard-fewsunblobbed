from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

from lizard_fewsunblobbed.views import FewsBrowserView

urlpatterns = patterns(
    '',
    url(r'^$',
        FewsBrowserView.as_view(),
        name="fews_browser",
        ),
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
