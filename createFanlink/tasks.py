from celery import shared_task
from .utils import setup_watch

@shared_task
def renew_watch(file_id, webhook_url):
    """Renew the watch periodically."""
    try:
        response = setup_watch(file_id, webhook_url)
        print("Watch renewed successfully:", response)
    except Exception as e:
        print("Error renewing watch:", str(e))
