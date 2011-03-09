"""
Retrieves fews unblobbed filter tree (and store it in the cache).
"""

from django.core.management.base import BaseCommand, CommandError
from lizard_fewsunblobbed.views import fews_filters
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ''
    help = 'Fill fews unblobbed filter cache'

    def handle(self, *args, **options):
        logger.info('Processing...')
        fews_filters(ignore_cache=True)
        logger.info('Finished successfully.')
