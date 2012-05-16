
from lizard_fewsunblobbed.views import fews_filters
from lizard_fewsunblobbed.models import Timeserie
from lizard_fewsunblobbed.models import Filter

from celery.task import task
from lizard_task.handler import get_handler

import logging


@task
def test_task(username=None, db_name=None, taskname=None):
    """
    Test task
    """
    handler = get_handler(username=username, taskname=taskname)
    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(20)

    logger.info('I did my job')
    return 'OK'


@task
def rebuild_unblobbed_cache(username=None, db_name=None, taskname=None):
    """
    Populate fews unblobbed cache for better user experience
    """
    handler = get_handler(username=username, taskname=taskname)
    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(20)

    logger.info('Processing filter tree...')
    fews_filters(ignore_cache=True)
    logger.info('Processing Timeserie.has_data_dict...')
    Timeserie.has_data_dict(ignore_cache=True)
    logger.info('Processing filters...')
    for f in Filter.objects.all():
        f.parameters()
    logger.info('Finished successfully.')

    return 'OK'
