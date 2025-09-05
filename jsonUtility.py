import json
import datetime
import csv
import os
import sql

import requests

from logger_config import *
from models import *

datetimeFormat = "%Y-%m-%dT%H:%M:%S"
timeCheck = 300 # Check every 300 seconds (in production)

JSON_FILE_SERVICES = "services.json"
services = Services.load_from_json_file(JSON_FILE_SERVICES)

def timeUpdate():
    with open("services.json", "r") as f:
        j = json.load(f)

    for k in j.keys():
        j[k]["Last access time"] = datetime.datetime.utcnow().strftime(datetimeFormat)

    with open("services.json", "w") as out:
        json.dump(j, out, indent=4, sort_keys=True, default=str)

def listServices():
    return services.names()

def statusUpdate():
    for service in listServices():
        service.refresh_status()
        
def deltaTime():
    logger.info("[LOG]: Deprecated")
    
    currentDate = datetime.datetime.utcnow()
    for k in listServices():
        pastDate = datetime.datetime.strptime(j[k]["Last access time"], datetimeFormat)
        print((currentDate - pastDate).total_seconds())
        
def deltaTimeService(services, service):
    if service not in services:
        logger.info("[LOG]: requested service is not tracked")
        return 0
    
    currentDate = datetime.datetime.utcnow()
    pastDate = datetime.datetime.strptime(services[service]["Last access time"], datetimeFormat)
    
    return (currentDate - pastDate).total_seconds() > timeCheck

def updateStatus(services, service, newStatus):
    services[service]["Last access time"] = datetime.datetime.utcnow().strftime(datetimeFormat)
    services[service]["Last status"] = newStatus
    
    with open("services.json", "w") as out:
        json.dump(services, out, indent=4, sort_keys=True, default=str)
        
def addNewService(service, url):
    #services.add_service(service, url)
    sql.add_new_service_entry(service)
        
def addBlankCSVService(service: Service):
    service = service.name
    filepath = "data/"
    cols = "date,UP\n"

    try:
        os.mkdir(filepath + service)        
        
    except FileExistsError:
        pass 
    except:
        raise ValueError(f"[LOG]: Something went wrong with creating the folder {service}")
    
    with open(filepath + service + "/log.csv", "w") as log:
        log.write(cols)        

def acceptRequest():
    with open("data\\request\\log.csv", "r") as f:
        read = csv.reader(f, delimiter=",")
        next(read, None)
        
        for row in read:
            addNewService(row[1], row[2])
            addBlankCSVService(row[1])
            
    
    with open("data\\request\\log.csv", "w") as f:
        f.write("time,service,url,reason\n")
        
def sync_services():
    # retrieve from UCLatence.be/extract?get=services
    response = requests.get("https://uclatence.be/extract?get=services")
    if response.status_code == 200:
        services_data = response.json()
        # Process the services_data as needed
    else:
        logger.error(f"[LOG]: Failed to retrieve services - {response.status_code}")
        
    with open("services.json", "w") as out:
        json.dump(services_data, out, indent=2, sort_keys=True, default=str)

if __name__ == "__main__":
    
    #acceptRequest()
    
    
    name = [ "Studies", "Mobi"]
    url = ["https://studies.uclouvain.be/", "https://app.uclouvain.be/Mobi"  ]
    
    """for i in range(len(name)):    
        addNewService(name[i], url[i])"""
    
    # Sync with UCLatence.be    
    sync_services()
    sql.sync_database()
        
    
    #print(deltaTimeService(j, "UCLouvain"))
    