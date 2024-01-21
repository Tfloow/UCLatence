import json
import datetime

datetimeFormat = "%d/%m/%Y %H:%M:%S"
timeCheck = 600 # Check every 300 seconds (in production)

def timeUpdate():
    with open("services.json", "r") as f:
        j = json.load(f)

    for k in j.keys():
        j[k]["Last access time"] = datetime.datetime.now().strftime(datetimeFormat)

    with open("services.json", "w") as out:
        json.dump(j, out, indent=4, sort_keys=True, default=str)

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

    currentDate = datetime.datetime.now()

    for k in j.keys():
        pastDate = datetime.datetime.strptime(j[k]["Last access time"], datetimeFormat)
        print((currentDate - pastDate).total_seconds())
        
def deltaTimeService(services, service):
    if service not in services:
        print("[LOG]: requested service is not tracked")
        return 0
    
    currentDate = datetime.datetime.now()
    pastDate = datetime.datetime.strptime(services[service]["Last access time"], datetimeFormat)
    
    return (currentDate - pastDate).total_seconds() > timeCheck

def updateStatus(services, service, newStatus):
    services[service]["Last access time"] = datetime.datetime.now().strftime(datetimeFormat)
    services[service]["Last status"] = newStatus
    
    with open("services.json", "w") as out:
        json.dump(services, out, indent=4, sort_keys=True, default=str)
        
if __name__ == "__main__":
    with open("services.json", "r") as f:
        j = json.load(f)
        
    print(deltaTimeService(j, "UCLouvain"))
    