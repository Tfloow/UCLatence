from flask import Flask, render_template, request, make_response, send_from_directory
import json
import requests
import csv
from apscheduler.schedulers.background import BackgroundScheduler # To schedule the check
import datetime
import atexit

# My modules
import jsonUtility
import dataReport

# Load JSON services
with open("services.json") as f:
    if f is None:
        raise ValueError("[LOG]: Error when opening the services.json")
    services = json.load(f)

def urlOfService(services, service):
    if service in services:
        return services[service]["url"]
    return "NaN"

def updateStatusService(services, service, session=None):
    url = urlOfService(services, service)
    if url == "NaN":
        print("[LOG]: You passed a service that is not tracked")
        return False
    
    print(f"[LOG]: HTTP request for {services[service]["url"]}")
    
    headers = {"User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"}
    if session is not None:
        # This line is sooooo slow
        response = session.head(url, headers=headers).status_code < 400  # Using a session to speed up refresh in a batch
    else:
        # This line is sooooo slow
        response = requests.head(url, headers=headers).status_code < 400 # Starting 400 codes are error for HTTP GET
    
    
    print("[LOG]: got status ")
    jsonUtility.updateStatus(services, service, response)
    dataReport.reportStatus(services, service)
    
    return response

def statusService(services, service):
    url = urlOfService(services, service)
    if url == "NaN":
        print("[LOG]: You passed a service that is not tracked")
        return False
    
    return services[service]["Last status"]

def refreshServices(services):
    print("[LOG]: Refreshing the services")
    session = requests.Session()
    
    for service in services.keys():
        updateStatusService(services, service, session)
    
    session.close()
    
    # To archive the current report daily to spare some memory
    dataReport.archiveStatus()

# Setup Scheduler to periodically check the status of the website
scheduler = BackgroundScheduler()
scheduler.add_job(refreshServices, "interval" ,args=[services], minutes=jsonUtility.timeCheck/60, next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=1))

# Start the scheduler
scheduler.start()

# When the scheduler need to be stopped
atexit.register(lambda: scheduler.shutdown())

# ------------------ Start the Flask app ------------------
app = Flask("UCLouvainDown")

@app.route("/")
def index():
    return render_template("index.html", serviceList=services.keys())

@app.route("/<service>")
def service(service):
    if service not in services.keys():
        return render_template("404.html")
    
    url = urlOfService(services, service)
    UP = statusService(services, service)
    
    return render_template("itemWebsite.html", service=service, url=url, UP=UP)

@app.route("/serviceList")
def serviceList():
    dictService = []
    
    for service in services:
        dictService.append(dict(service=service, url=services[service]["url"], reportedStatus=dataReport.getLastReport(service), Status=services[service]["Last status"]))
        
    return render_template("serviceList.html", serviceInfo=dictService)

@app.route("/request")
def requestServie():
    serviceName = request.args.get('service-name', "")
    url = request.args.get('url', "")
    info = request.args.get('info', "")
    
    # No form submitted No feedback
    feedback = "" 
            
    if len(serviceName) > 0:
        # If someone wrote in the form
        dataReport.newRequest(serviceName, url, info)
        feedback = "Form submitted successfully!"
    
    
    return render_template("request.html", feedback=feedback)

# To handle error reporting
@app.route('/process', methods=['GET'])
def process():
    user_choice = request.args.get('choice', 'default_value')
    service = request.args.get('service', None)
    
    

    if user_choice == 'yes':
        print('Great! The website is working for you.')
        
        if service is None:
            print("[LOG]: Something went wrong with the service reporting, please investigate")
        else:
            dataReport.addReport(service, True)
        
        return 'Great! The website is working for you.'
    elif user_choice == 'no':
        print('The website is down for me too.')
        
        if service is None:
            print("[LOG]: Something went wrong with the service reporting, please investigate")
        else:
            dataReport.addReport(service, False)
            
        return 'The website is down for me too.'
    else:
        return 'Invalid choice or no choice provided'
    
@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html")

@app.route("/extract")
def extractLog():
    get_what_to_extract = request.args.get("get")
    print(get_what_to_extract.split("_"))
    
    if get_what_to_extract.split("_")[0] in services.keys() or get_what_to_extract == "request":
        print("in keys")
        if len(get_what_to_extract.split("_")) > 1:
            # when we want to extract the past outages not the user outages
            path = "data/" + get_what_to_extract.split("_")[0] + "/outageReport.csv"
        else:
            path = "data/" + get_what_to_extract + "/log.csv"
            
        with open(path, "r") as file:
            csv_data = list(csv.reader(file, delimiter=","))
            
        response = make_response()
        csv_write = csv.writer(response.stream)
        csv_write.writerows(csv_data)
        
        response.headers["Content-Type"] = "text/csv"
        response.headers["Content-Disposition"] = f"attachment; filename={get_what_to_extract}.csv"
        
        return response
    else:
        return render_template("404.html")
    
@app.route('/robots.txt')
@app.route('/sitemap.xml')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])   

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)