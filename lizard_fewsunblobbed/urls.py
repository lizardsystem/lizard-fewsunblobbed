from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

from lizard_ui.urls import debugmode_urlpatterns
from lizard_fewsunblobbed.views import FewsBrowserView

urlpatterns = patterns(
    '',
    url(r'^$', FewsBrowserView.as_view(), name="fews_browser"),
)

if getattr(settings, 'LIZARD_FEWSUNBLOBBED_STANDALONE', False):
    admin.autodiscover()
    urlpatterns += patterns(
        '',
        url(r'^admin/', include(admin.site.urls)),
        (r'^map/', include('lizard_map.urls')),
    )
    urlpatterns += debugmode_urlpatterns()
