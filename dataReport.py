import jsonUtility
import os
from datetime import datetime
import pytz # For timezone

filepath = "data/"
cols = "date,UP\n"
serviceList = jsonUtility.listServices()

def addBlankCSV():    
    for service in serviceList:
        try:
            os.mkdir(filepath + service)        
            
        except FileExistsError:
            pass 
        except:
            raise ValueError(f"[LOG]: Something went wrong with creating the folder {service}")

    for service in serviceList:
        with open(filepath + service + "/log.csv", "w") as log:
                log.write(cols)

def addReport(service, user_choice):
    if service not in serviceList:
        print("[LOG]: we do not currently track the service")
        return False
        
    date = datetime.now(pytz.utc).strftime(jsonUtility.datetimeFormat)
    UP = str(user_choice)
        
    log = filepath + service + "/log.csv"
    
    with open(log, "a") as file:
        file.write(date + "," + UP + "\n")
    

if __name__ == "__main__":
    addBlankCSV()
    
    # For test purposes
    addReport("404-Test", datetime.now(), False)