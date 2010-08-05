import doctest

from django.test import TestCase

from lizard_fewsunblobbed.models import Filter
from lizard_fewsunblobbed.models import Location
from lizard_fewsunblobbed.models import Parameter
from lizard_fewsunblobbed.models import Timeserie
from lizard_fewsunblobbed.models import Timeseriedata
from lizard_fewsunblobbed import routers
from lizard_fewsunblobbed import views


class SmokeTest(TestCase):

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


# def suite():
#     """Return test suite

#     This method is automatically called by django's test mechanism.

#     """
#     return doctest.DocFileSuite(
#         'USAGE.txt',
#         'models.txt',
#         #'TODO_several_more_tests.txt',
#         module_relative=True,
#         optionflags=(doctest.NORMALIZE_WHITESPACE |
#                      doctest.ELLIPSIS |
#                      doctest.REPORT_NDIFF))
