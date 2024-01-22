from models import *

from flask import Flask, render_template, request, make_response
import json
import requests
import csv


# Load JSON file #######################################################################################################
JSON_FILE = "services.json"
services = Services.load_from_json_file(JSON_FILE)


# Start Flask app ######################################################################################################
app = Flask("UCLouvainDown")


@app.route("/")
async def index():
    """Render homepage, with an overview of all services."""
    print(f"[LOG]: HTTP request for homepage")
    services.refresh_status()
    return render_template("index.html", serviceList=services)


@app.route(f"/<any({[*services.names(), '']}):service>")
async def service_details(service: str):
    """Render a page with details of one service."""
    print(f"[LOG]: HTTP request for {service}")
    service_object = services.get_site(service)

    services.refresh_status(service)
    return render_template("itemWebsite.html", service=service_object)


@app.route("/<service>")
def service(service):
    if service not in services.keys():
        return render_template("404.html")
    
    url = urlOfService(services, service)
    UP = statusService(services, service)
    
    return render_template("itemWebsite.html", service=service, url=url, UP=UP)


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
    
    if get_what_to_extract in services.keys():
        with open("data/" + get_what_to_extract + "/log.csv", "r") as file:
            csv_data = list(csv.reader(file, delimiter=","))
            
        response = make_response()
        csv_write = csv.writer(response.stream)
        csv_write.writerows(csv_data)
        
        response.headers["Content-Type"] = "text/csv"
        response.headers["Content-Disposition"] = "attachment; filename=data.csv"
        
        return response
    else:
        return 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
