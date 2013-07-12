"""
Retrieves fews unblobbed filter tree (and store it in the cache).
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from lizard_fewsunblobbed.views import fews_filters
from lizard_fewsunblobbed.models import TimeSeriesKey
from lizard_fewsunblobbed.models import Filter
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ''
    help = 'Populate fews unblobbed cache for better user experience'

    def handle(self, *args, **options):
        logger.info('Using settings at %s', settings.SETTINGS_DIR)
        logger.info('CACHES = %s', settings.CACHES)
        logger.info('Processing filter tree...')
        fews_filters(ignore_cache=True)
        logger.info('Processing Timeserie.has_data_dict...')
        TimeSeriesKey.has_data_dict(ignore_cache=True)
        logger.info('Processing filters...')
        for f in Filter.objects.all():
            f.parameters(ignore_cache=True)
            Filter.get_related_filters_for(f.pk, ignore_cache=True)
        logger.info('Finished successfully.')
