from apscheduler.schedulers.blocking import BlockingScheduler
from models import *
from logger_config import *
import dataReport

JSON_FILE_WEBHOOKS = "webhooks.json"
webhooks = Webhooks.load_from_json_file(JSON_FILE_WEBHOOKS)

JSON_FILE_SERVICES = "services.json"
services = Services.load_from_json_file(JSON_FILE_SERVICES, webhooks=webhooks)
webhooks._set_services(webhooks)

def updateStatusService(service: str, session=None):
    url = services.get_service(service).url
    if not url:
        logger.info("[LOG]: You passed a service that is not tracked")
        return False
    
    logger.info(f"[LOG]: HTTP request for {url}")
    
    services.get_service(service).status_changed(session)

    logger.info("[LOG]: got status ")
    # REALLY IMPORTANT TO KEEP USING dataReport Library
    dataReport.reportStatus(services, service)
    
    return True

def refreshServices():
    logger.info("[LOG]: Refreshing the services")
    session = requests.Session()
    
    for service in services:
        logger.info(service)
        updateStatusService(service.name, session)

    session.close()

    logger.info("[LOG]: Finished Refreshing the services")
    
scheduler = BlockingScheduler()

# Execute the refreshServices function every RECHECK_AFTER minutes
@scheduler.scheduled_job("interval", seconds=RECHECK_AFTER)
def scheduledRefresh():
    refreshServices()
    
# Archive status at 3 AM UTC
@scheduler.scheduled_job("cron", hour=3, minute=0, second=0)
def scheduledArchive():
    dataReport.archiveStatus()
    
scheduler.start()