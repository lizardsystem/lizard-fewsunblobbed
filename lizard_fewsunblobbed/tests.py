from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from lizard_fewsunblobbed.models import Filter
from lizard_fewsunblobbed.models import Location
from lizard_fewsunblobbed.models import Parameter
from lizard_fewsunblobbed.models import Timeserie
from lizard_fewsunblobbed.models import Timeseriedata
from lizard_fewsunblobbed import routers
from lizard_fewsunblobbed import views


routers  # pyflakes
views  # pyflakes


class SmokeTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_available_and_empty(self):
        self.assertEquals(len(Filter.objects.all()), 0)
        self.assertEquals(len(Location.objects.all()), 0)
        self.assertEquals(len(Parameter.objects.all()), 0)
        self.assertEquals(len(Timeserie.objects.all()), 0)
        self.assertEquals(len(Timeseriedata.objects.all()), 0)

    def test_representation(self):
        filter_ = Filter()
        self.assertEquals(repr(filter_), '<Filter:  (id=)>')
        filter_.name = 'Sample filter'
        filter_.fews_id = '1234'
        self.assertEquals(repr(filter_), "<Filter: Sample filter (id=1234)>")

    def test_visit_fews_browser(self):
        url = reverse('fews_browser')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
