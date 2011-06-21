"""
Retrieves fews unblobbed filter tree (and store it in the cache).
"""

from django.core.management.base import BaseCommand
from django.db import connections, transaction
from lizard_fewsunblobbed.views import fews_filters
from lizard_fewsunblobbed.models import Timeserie
import logging
import datetime
import traceback
import sys

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ''
    help = 'Populate fews unblobbed cache for better user experience'

    @transaction.commit_manually(using='fews-unblobbed')
    def handle(self, *args, **options):
        logger.info('Copying data...')

        # Take correct cursor!
        cursor = connections['fews-unblobbed'].cursor()
        count = 0
        errors = 0
        # for tsd in Timeseriedata.objects.filter(
        #     tsd_time__gte=datetime.datetime(2010,6,1),
        #     tsd_time__lte=datetime.datetime(2010,7,20)):
        for ts in Timeserie.objects.all():
            for tsd in ts.timeseriedata.filter(
                tsd_time__gte=datetime.datetime(2010,6,1),
                tsd_time__lte=datetime.datetime(2010,6,20)):

                timestamp = tsd.tsd_time + datetime.timedelta(days=365)
                # which fields do we want to copy?
                try:
                    cursor.execute("insert into timeseriedata (tsd_time, tsd_value, tsd_flag, tsd_detection, tsd_comments, tkey) values (%s, %s, %s, %s, %s, %s)" , [timestamp.isoformat(), tsd.tsd_value, tsd.tsd_flag, tsd.tsd_detection, ('%s' % tsd.tsd_comments), ts.tkey])
                    transaction.commit(using='fews-unblobbed')
                    #transaction.commit_unless_managed(using='fews-unblobbed')

                    count += 1
                    if count % 1000 == 0:
                        logger.info('Copied... %d' % count)
                except:
                    transaction.rollback(using='fews-unblobbed')
                    errors += 1
                    if errors % 1000 == 0:
                        traceback.print_exc(file=sys.stdout)
                        logger.info('Errors (duplicates?)... %d' % errors)

                print "\r",count,

        logger.info('Copied: %d' % count)
        logger.info('Errors (duplicates?): %d' % errors)

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
