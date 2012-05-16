"""
Retrieves fews unblobbed filter tree (and store it in the cache).
"""

from django.core.management.base import BaseCommand
from lizard_fewsunblobbed.tasks import rebuild_unblobbed_cache


class Command(BaseCommand):
    args = ''
    help = 'Populate fews unblobbed cache for better user experience'

    def handle(self, *args, **options):
        return rebuild_unblobbed_cache()
