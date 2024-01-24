import json
import datetime
import pytz # For timezone
import csv
import os

datetimeFormat = "%Y-%m-%dT%H:%M:%S"
timeCheck = 600 # Check every 300 seconds (in production)

def timeUpdate():
    with open("services.json", "r") as f:
        j = json.load(f)

    for k in j.keys():
        j[k]["Last access time"] = datetime.datetime.now(pytz.utc).strftime(datetimeFormat)

    with open("services.json", "w") as out:
        json.dump(j, out, indent=4, sort_keys=True, default=str)

def listServices():
    with open("services.json", "r") as f:
        j = json.load(f)
    
    return j.keys()

def statusUpdate():
    with open("services.json", "r") as f:
        j = json.load(f)

    for k in j.keys():
        j[k]["Last status"] = True

    with open("services.json", "w") as out:
        json.dump(j, out, indent=4, sort_keys=True, default=str)
        
def deltaTime():
    with open("services.json", "r") as f:
        j = json.load(f)

    currentDate = datetime.datetime.now(pytz.utc)
    currentDate = currentDate.replace(tzinfo=None) # All values are not timezone Naive because the one saved and the one queried are UTC based

    for k in j.keys():
        pastDate = datetime.datetime.strptime(j[k]["Last access time"], datetimeFormat)
        print((currentDate - pastDate).total_seconds())
        
def deltaTimeService(services, service):
    if service not in services:
        print("[LOG]: requested service is not tracked")
        return 0
    
    currentDate = datetime.datetime.now(pytz.utc)
    currentDate = currentDate.replace(tzinfo=None)
    pastDate = datetime.datetime.strptime(services[service]["Last access time"], datetimeFormat)
    
    return (currentDate - pastDate).total_seconds() > timeCheck

def updateStatus(services, service, newStatus):
    services[service]["Last access time"] = datetime.datetime.now(pytz.utc).replace(tzinfo=None).strftime(datetimeFormat)
    services[service]["Last status"] = newStatus
    
    with open("services.json", "w") as out:
        json.dump(services, out, indent=4, sort_keys=True, default=str)
        
def addNewService(service, url):
    with open("services.json", "r") as f:
        j = json.load(f)
    
    j[service] = {}
    
    j[service]["url"] = url
    j[service]["Last access time"] = "2024-01-22T10:51:30" # Random date 
    j[service]["Last status"] = False
    
    with open("services.json", "w") as out:
        json.dump(j, out, indent=4, sort_keys=True, default=str)
        
def addBlankCSVService(service):
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
    
    acceptRequest()
    
    #print(deltaTimeService(j, "UCLouvain"))
    