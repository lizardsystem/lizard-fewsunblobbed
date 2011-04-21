from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from lizard_fewsunblobbed.layers import WorkspaceItemAdapterFewsUnblobbed
from lizard_fewsunblobbed.layers import fews_point_style
from lizard_fewsunblobbed.layers import fews_symbol_name
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

    def test_visit_fews_browser_filter(self):
        url = reverse('fews_browser') + '?filterkey=23467'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class AdapterTest(TestCase):

    def mock_timeseries():
        return {
            'rd_x': 500000,
            'rd_y': 200000,
            'object': None,
            'location_name': 'location.name',
            'name': 'name',
            'shortname': 'shortname',
            'workspace_item': None,
            'identifier': {'locationkey': 1},
            'google_coords': (0, 0),
            'has_data': True,
            }

    def setUp(self):
        self.mock_workspace_item = None
        self.adapter = WorkspaceItemAdapterFewsUnblobbed(
            self.mock_workspace_item,
            layer_arguments={'filterkey': 'filterkey',
                             'parameterkey': 'parameterkey'})
        self._timeseries = self.adapter._timeseries
        self.adapter._timeseries = self.mock_timeseries
        f = Filter(id=1, fews_id='default', name='default',
                   issubfilter=False, isendnode=True)
        f.save()

    def test_smoke(self):
        pass

    def test_fews_symbol_name(self):
        fews_symbol_name(1, nodata=False)
        fews_symbol_name(1, nodata=True)

    def test_fews_point_style(self):
        fews_point_style(1, nodata=False)
        fews_point_style(1, nodata=True)

    # def test_fews_timeserie(self):
    #     fews_timeserie('default', 'location', 'parameter')

    def tearDown(self):
        self.adapter._timeseries = self._timeseries

        # Necessary, because test_available_and_empty will else
        # fail. TODO: find out why
        Filter.objects.all().delete()


class FunctionTest(TestCase):

    def setUp(self):
        self.filters = [
            {'data': {'fews_id': 'fews_id_1'}, 'children': []},
            {'data': {'fews_id': 'fews_id_2'}},
            {'data': {'fews_id': 'fews_id_3'}, 'children': [
                    {'data': {'fews_id': 'fews_id_31'}, 'children': []},
                    {'data': {'fews_id': 'fews_id_32'}, 'children': []},
                    {'data': {'fews_id': 'fews_id_33'}, 'children': [
                            {'data': {'fews_id': 'fews_id_331'}},
                            ]},
                    {'data': {'fews_id': 'fews_id_34'}, 'children': []},
                    ]},
            {'data': {'fews_id': 'fews_id_4'}, 'children': []},
            ]

    def test_filter_exclude(self):
        exclude_filters = ['fews_id_2', 'fews_id_4', ]
        expected = [
            {'data': {'fews_id': 'fews_id_1'}, 'children': []},
            {'data': {'fews_id': 'fews_id_3'}, 'children': [
                    {'data': {'fews_id': 'fews_id_31'}, 'children': []},
                    {'data': {'fews_id': 'fews_id_32'}, 'children': []},
                    {'data': {'fews_id': 'fews_id_33'}, 'children': [
                            {'data': {'fews_id': 'fews_id_331'}},
                            ]},
                    {'data': {'fews_id': 'fews_id_34'}, 'children': []},
                    ]},
            ]
        result = views.filter_exclude(self.filters, exclude_filters)
        self.assertEqual(result, expected)

    def test_filter_exclude2(self):
        exclude_filters = ['fews_id_33', 'fews_id_4', ]
        expected = [
            {'data': {'fews_id': 'fews_id_1'}, 'children': []},
            {'data': {'fews_id': 'fews_id_2'}},
            {'data': {'fews_id': 'fews_id_3'}, 'children': [
                    {'data': {'fews_id': 'fews_id_31'}, 'children': []},
                    {'data': {'fews_id': 'fews_id_32'}, 'children': []},
                    {'data': {'fews_id': 'fews_id_34'}, 'children': []},
                    ]},
            ]
        result = views.filter_exclude(self.filters, exclude_filters)
        self.assertEqual(result, expected)
