from matplotlib.dates import date2num
import jsonUtility
import os
from datetime import datetime, time
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np

from logger_config import *

matplotlib.use('Agg')


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
    if not onlyOutageReport:
        logger.info("[LOG]: only plotting for user Report")
        toPlot = dict(userReport = filepath + service + "/log.csv")
    else:
        logger.info("[LOG]: only plotting for Report")
        toPlot = dict(outageReport = filepath + service + "/outageReport.csv")
    
    
    for report in toPlot:
        path = toPlot[report]
        
        size = os.path.getsize(path)
        
        fig,ax = plt.subplots()
        
        if len(cols) + 5 >= size:
            # It means we have just created the skeleton of the logs and there is no current logs
            text_kwargs = dict(ha='center', va='center', fontsize=28)
            
            fig.text(0.5, 0.5, 'No Data at The moment', **text_kwargs)
        else:
            # Great there is some data !
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
            
            timeArray = date2num(timeArray)
            
            timeNow = np.datetime64("now")
            
            points = np.array([timeArray, UPArray]).T.reshape(-1, 1, 2)
            segments = np.concatenate([points[:-1], points[1:]], axis=1)
            
            norm = plt.Normalize(0,1)
            lc = LineCollection(segments, cmap='RdYlGn', norm=norm)
            
            lc.set_array(UPArray)
            lc.set_linewidth(2)
            
            ax.add_collection(lc)
            #fig.colorbar(line, ax=axs[0])

            ax.set_ylim(-0.1,1.1)
            
            #ax.plot(timeArray, UPArray)
            ax.axvline(x=timeNow, linestyle="--", color="gray", alpha=0.5)
            ax.set_ylim(-0.1,1.1)
            
            now_kwargs = dict(color="red",ha='left', va='bottom')
            
            # To protect against unwanted behavior
            if timeArray.size > 2: 
                logger.info("[LOG]: temp fix")
                #ax.set_xlim(timeArray[0] - np.timedelta64(3, "m"), timeNow + np.timedelta64(3, "m"))
                #ax.text(timeNow - np.timedelta64((timeNow - timeArray[0]))*0.34 , 0.5, f"Last Report\n{timeNow}", **now_kwargs)
            else:
                ax.text(timeNow, 0.5, f"Last Report\n{timeNow}", **now_kwargs)
            
            if report == "userReport":
                ax.set_title(f"Status reported by users for {service}")
            else:
                ax.set_title(f"Past status for {service}")
            ax.set_ylabel("Up or Down")
            ax.set_xlabel("Date and Time (in UTC)")
            
        logger.info(f"[LOG]: PLOT --> service:{service} and report:{report}")
        if not onlyOutageReport:
            fig.savefig("static/img/log/" + service + ".png")
        else:
            fig.savefig("static/img/log/" + report + service + ".png")  
        
        # Important to avoid an ever increasing ram usage
        plt.close(fig) 
        
        logger.info("[LOG]: Finished plotting")

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
    
    os.system(f'cmd /c "curl {url}/extract?get=request -o data/request/log.csv"')
    os.system(f'cmd /c "curl {url}/extract?get=log -o my_log.log"')
    
    for service in serviceList:
        os.system(f'cmd /c "curl {url}/extract?get={service} -o data/{service}/log.csv"')
        os.system(f'cmd /c "curl {url}/extract?get={service}_outage -o data/{service}/outageReport.csv"')
        os.system(f'cmd /c "curl {url}/extract?get={service}_outage_archive -o data/{service}/outageReportArchive.csv"')
        
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
        
def reportStatus(services, service):
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
    logger.info("[LOG]: starting plot for outage")

    
    plot(service, True)
    logger.info("[LOG]: Finished plot for outage")
    
    logger.info("[LOG]: starting plot for user report")

    
    plot(service, False)
    logger.info("[LOG]: Finished plot for user report")
    

def archiveStatus():
    # We archive between 2 AM and 2 AM + time for a request
    start_archive = time(2, 0)
    end_archive = time(2, 5)
    currentTime = datetime.utcnow()


    if start_archive <= currentTime.time() <= end_archive:
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
            
            # Start with a fresh blank file
            with open(filepath + service + "/outageReport.csv", "w") as blankCurrent:
                blankCurrent.write(cols)
                
    
    

if __name__ == "__main__":
  dataExtraction()