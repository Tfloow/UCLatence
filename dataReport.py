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
                

def plot(service):
    path = filepath + service + "/log.csv"
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
        ax.set_xlim(timeArray[0] - np.timedelta64(3, "m"), timeNow + np.timedelta64(3, "m"))
        
        now_kwargs = dict(color="red",ha='left', va='bottom')
        ax.text(timeNow - np.timedelta64((timeNow - timeArray[0]))*0.34 , 0.5, f"Last Report\n{timeNow}", **now_kwargs)
        
        
        ax.set_title(f"Status reported by users for {service}")
        ax.set_ylabel("Up or Down")
        ax.set_xlabel("Date and Time")
     
    fig.savefig("static/img/log/" + service + ".png")  

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
        
        
        

if __name__ == "__main__":
    # addBlankCSV()
    
    # For test purposes
    # addReport("404-Test", datetime.now(), False)
    for service in serviceList:
        plot(service)