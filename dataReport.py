import jsonUtility
import os
from datetime import datetime
import pytz # For timezone
import matplotlib.pyplot as plt
import numpy as np

# Basic constant
filepath = "data/"
cols = "date,UP\n"
serviceList = jsonUtility.listServices()
url = "https://uclouvaindown-ed3979a045e6.herokuapp.com/"

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
                

def plot(service, onlyOutageReport=False):
    if not onlyOutageReport:
        print("[LOG]: also plotting for user Report")
        toPlot = dict(userReport = filepath + service + "/log.csv")
    else:
        toPlot = dict(outageReport = filepath + service + "/outageReport.csv")
    
    print(toPlot)
    
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
            data = np.genfromtxt(path, delimiter=",", names=True, dtype=dtypes, converters=converters)

            # Print the loaded data
            timeArray = data["date"]
            UPArray = data["UP"]
            
            timeNow = np.datetime64("now")
            
            ax.plot(timeArray, UPArray, marker = "o")
            ax.axvline(x=timeNow, linestyle="--", color="gray", alpha=0.5)
            
            now_kwargs = dict(color="red",ha='left', va='bottom')
            
            # To protect against unwanted behavior
            if timeArray.size > 2: 
                ax.set_xlim(timeArray[0] - np.timedelta64(3, "m"), timeNow + np.timedelta64(3, "m"))
                ax.text(timeNow - np.timedelta64((timeNow - timeArray[0]))*0.34 , 0.5, f"Last Report\n{timeNow}", **now_kwargs)
            else:
                ax.text(timeNow, 0.5, f"Last Report\n{timeNow}", **now_kwargs)
            
            if report == "userReport":
                ax.set_title(f"Status reported by users for {service}")
            else:
                ax.set_title(f"Past status for {service}")
            ax.set_ylabel("Up or Down")
            ax.set_xlabel("Date and Time")
        if not onlyOutageReport:
            toPlot = dict(userReport = filepath + service + "/outageReport.csv")
        else:
            fig.savefig("static/img/log/" + report + service + ".png")  

def addReport(service, user_choice):
    """Function to add a new line to the logs of each service

    Args:
        service (str): the name of the service
        user_choice (boolean): True if a service is up and running and False otherwise.

    Returns:
        _type_: _description_
    """
    if service not in serviceList:
        print("[LOG]: we do not currently track the service")
        return False
        
    date = datetime.now(pytz.utc).strftime(jsonUtility.datetimeFormat)
    UP = str(user_choice)
        
    log = filepath + service + "/log.csv"
    
    with open(log, "a") as file:
        file.write(date + "," + UP + "\n")
    
    plot(service) # To keep updated the graph         
        
        
def dataExtraction():
    # To get User's request
    os.system(f'cmd /c "curl {url}/extract?get=request -o data/request/log.csv"')
    
    for service in serviceList:
        os.system(f'cmd /c "curl {url}/extract?get={service} -o data/{service}/log.csv"')
        os.system(f'cmd /c "curl {url}/extract?get={service}_outage -o data/{service}/outageReport.csv"')
        
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
    date = datetime.now(pytz.utc).strftime(jsonUtility.datetimeFormat)
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
    
    print("[LOG]: starting Report")
    date = services[service]["Last access time"]
    UP = services[service]["Last status"]
    
    path = filepath + service + "/outageReport.csv"
    
    with open(path, "a") as out:
        out.write(date + "," + str(UP) + "\n")
    
    print("[LOG]: Finished Report")
    print("[LOG]: starting plot")

    
    plot(service, True)
    print("[LOG]: Finished plot")

    
    

if __name__ == "__main__":
    dataExtraction()