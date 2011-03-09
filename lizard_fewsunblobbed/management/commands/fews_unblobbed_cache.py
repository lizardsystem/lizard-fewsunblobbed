"""
Retrieves fews unblobbed filter tree (and store it in the cache).
"""

from django.core.management.base import BaseCommand, CommandError
from lizard_fewsunblobbed.views import fews_filters
from lizard_fewsunblobbed.models import Timeserie
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ''
    help = 'Populate fews unblobbed cache for better user experience'

    def handle(self, *args, **options):
        logger.info('Processing filter tree...')
        fews_filters(ignore_cache=True)
        logger.info('Processing Timeserie.has_data_dict...')
        Timeserie.has_data_dict(ignore_cache=True)
        logger.info('Finished successfully.')
