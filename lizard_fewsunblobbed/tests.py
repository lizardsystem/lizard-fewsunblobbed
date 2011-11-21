from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from lizard_fewsunblobbed.layers import WorkspaceItemAdapterFewsUnblobbed
from lizard_fewsunblobbed.models import IconStyle
from lizard_fewsunblobbed.models import Filter
from lizard_fewsunblobbed.models import Location
from lizard_fewsunblobbed.models import Parameter
from lizard_fewsunblobbed.models import Timeserie
from lizard_fewsunblobbed.models import Timeseriedata
from lizard_fewsunblobbed import routers
from lizard_fewsunblobbed import views


routers  # pyflakes


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
            layer_arguments={'filterkey': 1,
                             'parameterkey': 1},
            perform_existence_verification=False)
        self._timeseries = self.adapter._timeseries
        self.adapter._timeseries = self.mock_timeseries
        f = Filter(id=1, fews_id='default', name='default',
                   issubfilter=False, isendnode=True)
        f.save()

    def test_smoke(self):
        pass

    # def test_fews_symbol_name(self):
    #     fews_symbol_name(1, nodata=False)
    #     fews_symbol_name(1, nodata=True)

    # def test_fews_point_style(self):
    #     fews_point_style(1, nodata=False)
    #     fews_point_style(1, nodata=True)

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


class TestIconStyle(TestCase):
    """Based on tests in fewsjdbc"""

    def setUp(self):
        self.filter1 = Filter(
            id=1, fews_id='filter1', issubfilter=False, isendnode=False)
        self.filter2 = Filter(
            id=2, fews_id='filter2', issubfilter=False, isendnode=False)
        self.filter3 = Filter(
            id=3, fews_id='filter3', issubfilter=False, isendnode=False)
        self.location1 = Location(
            lkey=1, id='location1', x=0, y=0, z=0, longitude=0, latitude=0)
        self.location2 = Location(
            lkey=2, id='location2', x=0, y=0, z=0, longitude=0, latitude=0)
        self.location3 = Location(
            lkey=3, id='location3', x=0, y=0, z=0, longitude=0, latitude=0)
        self.parameter1 = Parameter(pkey=1, id='parameter1')
        self.parameter2 = Parameter(pkey=2, id='parameter2')
        self.parameter3 = Parameter(pkey=3, id='parameter3')

        self.filter1.save()
        self.filter2.save()
        self.filter3.save()
        self.location1.save()
        self.location2.save()
        self.location3.save()
        self.parameter1.save()
        self.parameter2.save()
        self.parameter3.save()

    # def test_styles(self):
    #     """See if styles() output correspond to database contents.
    #
    #     It seems that the database contains more IconStyles than the
    #     ones defined here. Strange??
    #     """
    #     IconStyle(fews_filter=None, fews_location=None, fews_parameter=None,
    #               icon='icon.png', mask='mask.png', color='ff00ff').save()
    #
    #     expected = {
    #         '::::':
    #         {'icon': 'icon.png', 'mask': ('mask.png', ),
    #          'color': (1.0, 0.0, 1.0, 1.0)}}
    #
    #     # You can see here that the database contains 10+ IconStyles...
    #     print IconStyle.objects.all()
    #     self.assertEqual(IconStyle._styles(), expected)
    #
    #
    # def test_styles(self):
    #     """See if styles_lookup() output correspond to database contents.
    #
    #     It seems that the database contains more IconStyles than the
    #     ones defined here. Strange??
    #     """
    #     IconStyle(fews_filter=None, fews_location=None, fews_parameter=None,
    #               icon='icon.png', mask='mask.png', color='ff00ff').save()
    #     IconStyle(fews_filter=self.filter1,
    #               fews_location=None, fews_parameter=None,
    #               icon='filter1.png', mask='mask.png', color='ff00ff').save()
    #
    #     expected = {
    #         '::::':
    #         {'icon': 'icon.png', 'mask': ('mask.png', ),
    #          'color': (1.0, 0.0, 1.0, 1.0)},
    #         '%d::::' % (self.filter1.pk):
    #         {'icon': 'filter1.png', 'mask': ('mask.png', ),
    #          'color': (1.0, 0.0, 1.0, 1.0)}}
    #
    #     # You can see here that the database contains 10+ IconStyles...
    #     print IconStyle.objects.all()
    #
    #     self.assertEqual(IconStyle._styles(), expected)

    def test_lookup(self):
        IconStyle(fews_filter=None, fews_location=None, fews_parameter=None,
                  icon='icon.png', mask='mask.png',
                  color='ff00ff').save()
        IconStyle(fews_filter=self.filter1,
                  fews_location=None, fews_parameter=None,
                  icon='filter1.png', mask='mask.png', color='ff00ff').save()
        IconStyle(fews_filter=None,
                  fews_location=self.location1,
                  fews_parameter=self.parameter1,
                  icon='loc1par1.png', mask='mask.png', color='00ffff').save()
        IconStyle(fews_filter=None,
                  fews_location=self.location1,
                  fews_parameter=None,
                  icon='loc1.png', mask='mask.png', color='00ffff').save()

        expected = {
            # Level0: fews_filter
            None: {
                # Level1: fews_location
                None: {
                    # Level2: fews_parameter
                    None: '::::'
                   },
                self.location1.pk: {
                    # Level2: fews_parameter
                    None: '::%d::' % self.location1.pk,
                    self.parameter1.pk: '::%d::%d' % (
                        self.location1.pk, self.parameter1.pk)
                   }
                },
            self.filter1.pk: {
                # Level1: fews_location
                None: {
                    # Level2: fews_parameter
                    None: '%d::::' % self.filter1.pk
                   }
                }
            }

        self.assertEqual(IconStyle._lookup(), expected)

    def test_style(self):
        """See if style() output correspond to expected lookup.
        """
        IconStyle(fews_filter=None, fews_location=None, fews_parameter=None,
                  icon='icon.png', mask='mask.png', color='ff00ff').save()
        IconStyle(fews_filter=self.filter1,
                  fews_location=None, fews_parameter=None,
                  icon='filter1.png', mask='mask.png', color='00ffff').save()
        IconStyle(fews_filter=None,
                  fews_location=self.location1, fews_parameter=None,
                  icon='par1.png', mask='mask.png', color='00ffff').save()
        IconStyle(fews_filter=self.filter1, fews_location=self.location1,
                  fews_parameter=None,
                  icon='loc1.png', mask='mask.png', color='00ffff').save()
        IconStyle(fews_filter=self.filter1, fews_location=self.location1,
                  fews_parameter=self.parameter1,
                  icon='par1.png', mask='mask.png', color='00ffff').save()
        IconStyle(fews_filter=None, fews_location=self.location1,
                  fews_parameter=self.parameter1,
                  icon='loc1par1.png', mask='mask.png', color='00ffff').save()

        expected1 = (
            '::::',
            {'icon': 'icon.png', 'mask': ('mask.png', ),
             'color': (1.0, 0.0, 1.0, 1.0)})
        self.assertEqual(
            IconStyle.style(self.filter2, self.location2, self.parameter2),
            expected1)
        self.assertEqual(
            IconStyle.style(self.filter2, self.location2, self.parameter2,
                            ignore_cache=True),
            expected1)

        # It seems that IconStyles defined in other tests are also
        # available here...

        # expected2 = (
        #     '%d::::' % self.filter1.pk,
        #     {'icon': 'filter1.png', 'mask': ('mask.png', ),
        #      'color': (0.0, 1.0, 1.0, 1.0)})
        # self.assertEqual(
        #     IconStyle.style(self.filter1, self.location2, self.parameter2),
        #     expected2)
        # self.assertEqual(
        #     IconStyle.style(self.filter1, self.location2, self.parameter2,
        #                     ignore_cache=True),
        #     expected2)

        # expected3 = (
        #     '%d::%d::' % (self.filter1.pk, self.location1.pk),
        #     {'icon': 'loc1.png', 'mask': ('mask.png', ),
        #      'color': (0.0, 1.0, 1.0, 1.0)})
        # self.assertEqual(
        #     IconStyle.style(self.filter1, self.location1, self.parameter2),
        #     expected3)

        # expected4 = (
        #     '%d::%d::%d' % (
        #         self.filter1.pk, self.location1.pk, self.parameter1.pk),
        #     {'icon': 'par1.png', 'mask': ('mask.png', ),
        #      'color': (0.0, 1.0, 1.0, 1.0)})
        # self.assertEqual(
        #     IconStyle.style(self.filter1, self.location1, self.parameter1),
        #     expected4)

        # expected5 = (
        #     '::%d::%d' % (self.location1.pk, self.parameter1.pk),
        #     {'icon': 'loc1par1.png', 'mask': ('mask.png', ),
        #      'color': (0.0, 1.0, 1.0, 1.0)})
        # self.assertEqual(
        #     IconStyle.style(self.filter2, self.location1, self.parameter1),
        #     expected5)

    def test_empty(self):
        """Do not crash when no iconstyles are available, just return default.
        """

        expected = (
            '::::',
            {'icon': 'meetpuntPeil.png', 'mask': ('meetpuntPeil_mask.png', ),
             'color': (0.0, 0.5, 1.0, 1.0)})

        self.assertEqual(
            IconStyle.style(self.filter2, self.location1, self.parameter1),
            expected)

    # def test_not_found(self):
    #     """Do not crash when corresponding iconstyle is not available.

    #     Just return default.

    #     It seems that IconStyles defined in other tests are also
    #     available here...
    #     """
    #     IconStyle(fews_filter=self.filter1,
    #               fews_location=None, fews_parameter=None,
    #               icon='filter1.png', mask='mask.png', color='00ffff').save()

    #     expected = (
    #         '::::',
    #         {'icon': 'meetpuntPeil.png', 'mask': ('meetpuntPeil_mask.png', ),
    #          'color': (0.0, 0.5, 1.0, 1.0)})

    #     self.assertEqual(
    #         IconStyle.style(self.filter3, self.location3, self.parameter3),
    #         expected)
