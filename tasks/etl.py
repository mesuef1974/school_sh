
from celery import shared_task

@shared_task
def import_operational_plan_items():
    # TODO: قراءة CSV من access_raw أو مسار محدد، وإدخالها عبر ORM
    return {'status':'ok'}
