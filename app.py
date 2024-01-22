"""
TODO ajouter inginious
"""
from enum import Enum
from typing import Annotated

import uvicorn as uvicorn
from fastapi.responses import JSONResponse
from flask import Flask, render_template
from fastapi import FastAPI, Path
from fastapi.middleware.wsgi import WSGIMiddleware


from flask import Flask, render_template, request, make_response, send_from_directory
import json
import requests
import csv

import dataReport
from models import *
from fastapi_custom import *


# Load JSON file #######################################################################################################
JSON_FILE = "services.json"
services = Services.load_from_json_file(JSON_FILE)


# Define the Flask app and its routes ##################################################################################
app = Flask("UCLouvainDown")


@app.route("/")
async def index():
    """Render homepage, with an overview of all services."""
    print(f"[LOG]: HTTP request for homepage")
    return render_template("index.html", serviceList=(await all_service_details()).root)


@app.route(f"/<any({[*services.names(), '']}):service>")
async def service_details_app(service: str):
    """Render a page with details of one service."""
    print(f"[LOG]: HTTP request for {service}")
    return render_template("itemWebsite.html", service=await service_details(service))

@app.route("/serviceList")
def serviceList():
    dictService = []
    
    for service in services:
        dictService.append(dict(service=service, url=services[service]["url"], reportedStatus=dataReport.getLastReport(service), Status=services[service]["Last status"]))
        
    return render_template("serviceList.html", serviceInfo=dictService)

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
    
@app.route('/robots.txt')
@app.route('/sitemap.xml')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


# Define the FastAPI app ###############################################################################################
api = FastAPI(
    title="UCLouvainDown API",
    version="v0.1.0",
    summary="**A simple interface with the *UCLouvainDown* backend!**",
    description="This API provides an interface with the *UCLouvainDown* backend, allowing to check if services of the "
                "University of Louvain (UCLouvain), as well as some other services often used by students, "
                "are up and running (or not). Non-developpers might be better of using the [UCLouvainDown website](/) "
                "rather than passing by this API.",
    docs_url=None,
    redoc_url="/api/redoc",
    # terms_of_service="", TODO
    contact={
        "name": "Wouter Vermeulen",
        "email": "wouter.vermeulen@student.uclouvain.be",
    },
    # license_info={}, TODO
)
api_404_response = JSONResponse(
    content={"error": "Not found",
             "detail": "Sorry, could not find the URL. Please check the documentation at '/api/redoc'!"}
)


# Couple the Flask app and the FastAPI app #############################################################################
# !!! DO NOT move the `api.mount` statement before the `@api....` functions !!! ########################################
SupportedServices = Enum("SupportedServices", {service: service for service in services.names()})


# TODO check if remotely correct in regards of the openapi spec (whatever the case, it does look clean :<) )
@api.get("/api/services/overview", response_model=List[str], openapi_extra={"responses": {"200": {
            "description": "Successful Response", "content": {
              "application/json": {
                "schema": {
                  "items": {
                    "type": "string",
                    "description": "The name of a tracked service",
                  },
                  "type": "array",
                  "examples": [["Inginious", "ADE-scheduler"]]
                }}}}}})
def services_overview():
    """
    Get a list of the names of all services that are tracked (that is, regularly checked on their status) by this
    application. This are the only names accepted in requests requiring a service name, such as for example
    [`service_details`](/api/redoc#operation/service_details).
    """
    return services.names()


# TODO check if remotely correct in regards of the openapi spec (whatever the case, it does look clean :<) )
@api.get("/api/services/up/all", response_model=Dict[str, bool], openapi_extra={"responses": {"200": {
    "description": "Successful Response", "content": {
              "application/json": {
                "schema": {
                    "type": "dictionary",
                    "title": None,
                    "description": "Keys are the name of a tracked service, values are booleans: `true` means the "
                                   "service is up and running, `false` means it is down.",
                    "examples": [{"Inginious": True, "ADE-scheduler": False}]
                }}}}}})
async def all_service_statuses():
    """
    Get the current status (up or down) for all tracked services.

    **Note**: *for most applications, the status for only a few services are needed. Please use the
      [`Service Status` endpoint](/api/redoc#operation/service_status) instead in those cases!*

    **Note**: *a status change might be reported with a small delay. Applications requiring 100% up-to-date
    information that wish the verify when the status was last checked, should use the
     [`All Service Details` endpoint](/api/redoc#operation/all_service_details) or the
     [`Service Details` endpoint](/api/redoc#operation/service_details).*
    """
    await services.refresh_status()
    return {service.name: service.is_up for service in services}


@api.get("/api/services/up/<service:str>", response_model=bool, openapi_extra={"responses": {"200": {
    "description": "Successful Response", "content": {
              "application/json": {
                "schema": {
                    "type": "boolean",
                    "title": None,
                    "description": "The status of the service: `true` if the service is up and running, "
                                   "`false` if it is down.",
                    "examples": [True, False]
                }}}}}
})
async def service_status(
        service: Annotated[
            SupportedServices,
            Path(
                description="The service for which to get the status. It must be in the list of tracked services"
                            "that can be requested at [this endpoint](/api/redoc#operation/services_overview).")]):
    """
    Get the status of a specific service.

    **Note**: *a status change might be reported with a small delay. Applications requiring 100% up-to-date
    information that wish the verify when the status was last checked, should use the
     [`Service Details` endpoint](/api/redoc#operation/service_details).*
    """
    service_object = services.get_service(service)
    await services.refresh_status(service)
    return service_object.is_up


@api.get("/api/services/all", response_model=Services)
async def all_service_details():
    """
    Get the following information on all tracked services:
      * The service url.
      * The current status of the service: is the service up or down (a status change might be reported with a small
        delay - for applications requiring 100% up-to-date information be sure to verify that the `last_checked` field
        in the response is recent enough).
      * The last time the status of the service was checked.

    **Note**: *for most applications, the details for only a few services are needed. Please use the
      [`service details endpoint`](/api/redoc#operation/service_details) instead in those cases!*
    """
    await services.refresh_status()
    return services


@api.get("/api/services/<service:str>", response_model=Service)
async def service_details(
        service: Annotated[
            SupportedServices,
            Path(
                description="The service for which to get the information. It must be in the list of tracked services"
                            "that can be requested at [this endpoint](/api/redoc#operation/services_overview).")]):
    """
    Get the following information on a service by passing its name:
      * The service url.
      * The current status of the service: is the service up or down (a status change might be reported with a small
        delay - for applications requiring 100% up-to-date information be sure to verify that the `last_checked` field
        in the response is recent enough).
      * The last time the status of the service was checked.

    **Note:** *a list of all tracked services can be found at [this endpoint](/api/redoc#operation/services_overview).*

    \f

    Service shall be a valid service, werkzeug already checks this for us with the enumeration of supported services.
    """
    service_object = services.get_service(service)
    await services.refresh_status(service)
    return service_object


@api.api_route("/api", status_code=404, include_in_schema=False)
def api_request_not_found() -> JSONResponse:
    """
    Any paths with `/api` and `/api/...` that have not been catched before are invalid.
    If this endpoint wasn't added, the client would recieve the 404 HTML site from the UCLouvainDown website.

    Note: tried to implement this in `api.py`, however that didn't work, don't really know why.
    """
    return api_404_response


@api.api_route("/api/{_:path}", status_code=404, include_in_schema=False)
def error_404(_: str = "") -> JSONResponse:
    return api_request_not_found()


api.mount("/", WSGIMiddleware(app))


# Modify the openapi docs a little #####################################################################################
use_route_names_as_operation_ids(api)


# Run the whole application ############################################################################################
if __name__ == "__main__":
    uvicorn.run(api)
    # app.run(host="0.0.0.0", debug=True)
