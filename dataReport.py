import jsonUtility
import os
from datetime import datetime, time,timezone
import numpy as np

from logger_config import *



from models import *

# Basic constant
filepath = "data/"
cols = "date,UP\n"
JSON_FILE_SERVICES = "services.json"
services = Services.load_from_json_file(JSON_FILE_SERVICES)
serviceList = services.names
url = "https://www.uclouvain-down.be"

def addService(name: str) -> bool:
    try:
        os.mkdir(filepath + name)        
        
    except FileExistsError:
        pass 
    except:
        raise ValueError(f"[LOG]: Something went wrong with creating the folder {name}")
    
    with open(filepath + name + "/log.csv", "w") as log:
        log.write(cols)
        
    with open(filepath + name + "/outageReport.csv", "w") as out:
        out.write(cols)
    

def addBlankCSV():
    """Simple utility that is use to generate a skeleton of logs

    Raises:
        ValueError: If we encounter an error other than trying to create an existing directory
    """
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
        with open(filepath + service + "/outageReport.csv", "w") as log:
                log.write(cols)
        with open(filepath + service + "/outageReportArchive.csv", "w") as log:
                log.write(cols)

def dummyData():
    data = "date,UP\n2024-01-25T02:21:35,True\n2024-01-25T02:21:35,True\n2024-01-25T02:31:35,True\n"
    for service in serviceList:
        try:
            os.mkdir(filepath + service)        
            
        except FileExistsError:
            pass 
        except:
            raise ValueError(f"[LOG]: Something went wrong with creating the folder {service}")

    for service in serviceList:
        with open(filepath + service + "/log.csv", "w") as log:
                log.write(data)
        with open(filepath + service + "/outageReport.csv", "w") as log:
                log.write(data)
        with open(filepath + service + "/outageReportArchive.csv", "w") as log:
                log.write(data)
                
def plot(service, onlyOutageReport=False):
    logger.info("[LOG]: Deprecated plot function")
    return


def addReport(service, user_choice):
    """Function to add a new line to the logs of each service

    Args:
        service (str): the name of the service
        user_choice (boolean): True if a service is up and running and False otherwise.

    Returns:
        _type_: _description_
    """
    if service not in serviceList:
        logger.info("[LOG]: we do not currently track the service")
        return False
        
    date = datetime.utcnow().strftime(jsonUtility.datetimeFormat)
    UP = str(user_choice)
        
    log = filepath + service + "/log.csv"
    
    with open(log, "a") as file:
        file.write(date + "," + UP + "\n")
    
    # Was causing bugs
    #plot(service) # To keep updated the graph         
        
        
def dataExtraction():
    # To get User's request
    # check if it is windows or linux
    print(os.name)
    if os.name == "nt":
        
        os.system(f'cmd /c "curl {url}/extract?get=request -o data/request/log.csv"')
        os.system(f'cmd /c "curl {url}/extract?get=log -o my_log.log"')
        
        for service in serviceList:
            os.system(f'cmd /c "curl {url}/extract?get={service} -o data/{service}/log.csv"')
            os.system(f'cmd /c "curl {url}/extract?get={service}_outage -o data/{service}/outageReport.csv"')
            os.system(f'cmd /c "curl {url}/extract?get={service}_outage_archive -o data/{service}/outageReportArchive.csv"')
    else:
        os.system(f"curl {url}/extract?get=request -o data/request/log.csv")
        os.system(f"curl {url}/extract?get=log -o my_log.log")
        
        for service in serviceList:
            os.system(f"curl {url}/extract?get={service} -o data/{service}/log.csv")
            os.system(f"curl {url}/extract?get={service}_outage -o data/{service}/outageReport.csv")
            os.system(f"curl {url}/extract?get={service}_outage_archive -o data/{service}/outageReportArchive.csv") 
        
def getLastReport(service):
    with open("data/" + service + "/log.csv", "r") as file:
        f = file.readlines()
        lastValue = f[-1].split(",")[1].strip("\n") 
        

        if lastValue == "False":
            return False
        if lastValue == "True":
            return True
        return None

def newRequest(serviceName, url, info):
    date = datetime.utcnow().strftime(jsonUtility.datetimeFormat)
    log = "data/request/log.csv"
    
    with open(log, "a") as file:
        file.write(date + "," + serviceName + "," + url + "," + info + "\n")

def blankStatus():
    for service in serviceList:
        try:
            os.mkdir(filepath + service)        
            
        except FileExistsError:
            pass 
        except:
            raise ValueError(f"[LOG]: Something went wrong with creating the folder {service}")

    for service in serviceList:
        with open(filepath + service + "/outageReport.csv", "w") as log:
            log.write(cols)
        
def reportStatus(services, service, PLOT=False):
    """Add the log of the current status of the site so we can track it throughout time

    Args:
        services (dict): the loaded services.json
        service (string): the specific service we want to report
    """
    
    logger.info("[LOG]: starting Report")
    serviceObject = services.get_service(service)
    logger.info(serviceObject)
    date = serviceObject.last_checked
    UP = serviceObject.is_up
    
    path = filepath + service + "/outageReport.csv"
    
    with open(path, "a") as out:
        out.write(date.strftime(jsonUtility.datetimeFormat) + "," + str(UP) + "\n")
    
    logger.info(f"[LOG]: Finished Report at {path}")
    
def archiveStatus():
    logger.info("[LOG]: Starting archiving")
    
    for service in serviceList:
        # Check if there is a file to report the archive
        if not os.path.exists(filepath + service + "/outageReportArchive.csv"):
            with open(filepath + service + "/outageReportArchive.csv", "w") as newArchive:
                newArchive.write(cols)
        
        # Open the old file
        with open(filepath + service + "/outageReport.csv", "r") as current:
            content = current.readlines()[1:] # Remove the head of the csv
                
        # Append it to the archive
        with open(filepath + service + "/outageReportArchive.csv", "a") as archive:
            archive.writelines(content)
            
        # Extra Precaution
        open(filepath + service + "/outageReport.csv", "w").close()
        
        # Start with a fresh blank file
        with open(filepath + service + "/outageReport.csv", "w") as blankCurrent:
            blankCurrent.write(cols)

def dataForChart(service):
    path = filepath + service + "/outageReport.csv"
    
    size = os.path.getsize(path)
    
    if size == len(cols):
        return None
    
    # Define a custom converter for the date column
    date_converter = lambda x: np.datetime64(x.decode("utf-8"))
    
    # Specify the data types and converters for each column
    dtypes = np.dtype([("date", "datetime64[s]"), ("UP", "bool")])
    converters = {"date": date_converter}

    # Load the CSV file into a NumPy array
    logger.info(f"[LOG]: trying to open data from {path}")
    data = np.genfromtxt(path, delimiter=",", names=True, dtype=dtypes, converters=converters)

    # Print the loaded data
    timeArray = data["date"]
    UPArray = data["UP"]
    
    #timeArray = date2num(timeArray)
    
    UPArray = np.where(UPArray == True, 1, 0)
    
    # Doing the same but for log.csv
    path = filepath + service + "/log.csv"
    
    size = os.path.getsize(path)
    
        
    if size == len(cols):
        return None
    
    # Define a custom converter for the date column
    date_converter = lambda x: np.datetime64(x.decode("utf-8"))
    
    # Specify the data types and converters for each column
    dtypes = np.dtype([("date", "datetime64[s]"), ("UP", "bool")])
    converters = {"date": date_converter}

    # Load the CSV file into a NumPy array
    logger.info(f"[LOG]: trying to open data from {path}")
    data = np.genfromtxt(path, delimiter=",", names=True, dtype=dtypes, converters=converters)

    # Print the loaded data
    timeArray_user = data["date"]
    UPArray_user = data["UP"]
    
    #timeArray_user = date2num(timeArray_user)
    
    UPArray_user = np.where(UPArray_user == True, 1, 0)
    
    return (timeArray, UPArray), (timeArray_user, UPArray_user)

def overallUpTime(service):
    # Open the outageReportArchive and do a summary
    path = filepath + service + "/outageReportArchive.csv"
    
    size = os.path.getsize(path)
    
    if size == len(cols):
        return None
    
    # Define a custom converter for the date column
    date_converter = lambda x: np.datetime64(x.decode("utf-8"))
    
    # Specify the data types and converters for each column
    dtypes = np.dtype([("date", "datetime64[s]"), ("UP", "bool")])
    converters = {"date": date_converter}

    # Load the CSV file into a NumPy array
    logger.info(f"[LOG]: trying to open data from {path}")
    data = np.genfromtxt(path, delimiter=",", names=True, dtype=dtypes, converters=converters)
    
    UPArray = data["UP"]
    UPArray = np.where(UPArray == True, 1, 0)
    
    count_up = np.count_nonzero(UPArray)
    count_down = len(UPArray) - count_up
    
    return count_up/len(UPArray), count_down/len(UPArray)


if __name__ == "__main__":
  dataExtraction()