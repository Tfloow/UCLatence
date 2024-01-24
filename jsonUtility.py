import json
import datetime
import csv
import os
from models import *

datetimeFormat = "%Y-%m-%dT%H:%M:%S"
timeCheck = 600 # Check every 300 seconds (in production)

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
    print("[LOG]: Deprecated")
    
    currentDate = datetime.datetime.utcnow()
    for k in listServices():
        # pastDate = datetime.datetime.strptime(j[k]["Last access time"], datetimeFormat)
        print((currentDate - pastDate).total_seconds())
        
def deltaTimeService(services, service):
    if service not in services:
        print("[LOG]: requested service is not tracked")
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
    services.add_service(service, url)
        
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
    
        
if __name__ == "__main__":
    
    #acceptRequest()
    
    """
    name = [ "Inginious","UDS", "UCLSport","LEPL1104","LEPL1201"]
    url = ["https://inginious.info.ucl.ac.be/","https://uds.siws.ucl.ac.be/","https://sites.uclouvain.be/uclsport/",
           "https://perso.uclouvain.be/vincent.legat/zouLab/epl1104.php","https://perso.uclouvain.be/vincent.legat/zouLab/epl1201.php" ]
    
    for i in range(len(name)):    
        services.add_service(name[i], url[i])
    """
    #print(deltaTimeService(j, "UCLouvain"))
    