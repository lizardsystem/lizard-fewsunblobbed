"""
Retrieves fews unblobbed filter tree (and store it in the cache).
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from lizard_fewsunblobbed.views import fews_filters
from lizard_fewsunblobbed.models import Timeseriedata
import logging
import datetime


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ''
    help = 'Populate fews unblobbed cache for better user experience'

    def handle(self, *args, **options):
        logger.info('Copying june 2010 ... data...')

        cursor = connection.cursor()
        count = 0
        for tsd in Timeseriedata.objects.filter(
            tsd_time__gte=datetime.datetime(2010,6,1),
            tsd_time__lte=datetime.datetime(2010,7,20)):

            timestamp = tsd.tsd_time + datetime.timedelta(days=365)
            # which fields do we want to copy?
            cursor.execute("insert into timeseriedata (tsd_time, tsd_value, tsd_flag, tsd_detection, tsd_comments, tkey) values (%s, %s, %s, %s, %s, %s)" , [timestamp.isoformat(), tsd.tsd_value, tsd.tsd_flag, True, ('%s'%tsd.tsd_comments), tsd.tkey.pk])

            count += 1
            if count % 1000 == 0:
                logger.info('Data... %d' % count)
            print "\r",count,

        transaction.commit_unless_managed()

        # for timeserie in Timeserie.objects.all():
        #     logger.info('Timeserie: %s' % timeserie)

        # timeserie.timeseriedata_set.all()

        # This was supposed to work, but is doesn't.
        # ValidationError: [u'Enter a valid date/time in
        # YYYY-MM-DD HH:MM[:ss[.uuuuuu]] format.']

        # >>> from copy import deepcopy
        # >>> new_tsd = deepcopy(tsd)
        # >>> new_tsd.id = None
        # >>> new_tsd.tsd_time
        # datetime.datetime(2010, 6, 3, 6, 15)
        # >>> new_tsd.tsd_time += datetime.timedelta(days=365)
        # >>> new_tsd.save()
