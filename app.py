try:
    import uvicorn as uvicorn

    from fastapi import APIRouter, FastAPI, Path, Request
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse
    from fastapi.middleware.wsgi import WSGIMiddleware

    from flask import Flask, render_template, request, make_response, send_from_directory

    import csv
    from apscheduler.schedulers.background import BackgroundScheduler # To schedule the check
    import datetime
    import logging
    
        # Own modules
    # import dataReport
    from models import *
    from fastapi_custom import ALL_HTTP_METHODS, hide_422, hide_default_responses, use_route_names_as_operation_ids
    from utilities import *
    
    # For compatibility
    import dataReport
    import jsonUtility
except ImportError:
    print("[LOG] Error on startup: not all packages could be properly imported.")
    raise exit(1)
except ImportWarning as w:
    print(f"[LOG] Warning on startup: not all packages could be properly imported:\n{w}")


# Load JSON files ######################################################################################################
JSON_FILE_WEBHOOKS = "webhooks.json"
webhooks = Webhooks.load_from_json_file(JSON_FILE_WEBHOOKS)

def urlOfService(services, service):
    if service in services.names():
        return services.get_service(service).url
    return "NaN"

def updateStatusService(services, service, session=None):
    url = urlOfService(services, service)
    if url == "NaN":
        print("[LOG]: You passed a service that is not tracked")
        return False
    
    print(f"[LOG]: HTTP request for {url}")
    
    services.get_service(service).refresh_status(session)
    
    
    print("[LOG]: got status ")
    dataReport.reportStatus(services, service)
    
    return True

def statusService(services, service):
    url = urlOfService(services, service)
    if url == "NaN":
        print("[LOG]: You passed a service that is not tracked")
        return False
    
    return services[service]["Last status"]

def refreshServices(services):
    print("[LOG]: Refreshing the services")
    session = requests.Session()
    
    for service in services.names():
        print(service)
        updateStatusService(services, service, session)

# Setup Scheduler to periodically check the status of the website
scheduler = BackgroundScheduler()
scheduler.add_job(refreshServices, "interval" ,args=[services], minutes=jsonUtility.timeCheck/60, next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=1))

# Start the scheduler
scheduler.start()

# ------------------ Start the Flask app ------------------
app = Flask("UCLouvainDown")


@app.route("/")
async def index():
    """Render homepage, with an overview of all services."""
    print(f"[LOG]: HTTP request for homepage")
    return render_template("index.html", serviceList=all_service_details().root)


@app.route(f"/<any({[*services.names(), '']}):service>")
async def service_details_app(service: str):
    """Render a page with details of one service."""
    print(f"[LOG]: HTTP request for {service}")
    return render_template("itemWebsite.html", service=service_details(service))

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
    log = False
    if len(get_what_to_extract.split("_")) > 1 and services.get_service(get_what_to_extract) is not None:
        # it means we want the outage log not the user's log
        log = True
    
    if services.get_service(get_what_to_extract) is not None or get_what_to_extract == "request" or log:
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


# Define the FastAPI app and its routes ################################################################################
# !!! DO NOT move the `api.mount(...)` statement before the `@api....` functions !!! ###################################
api = FastAPI(
    title="UCLouvainDown API",
    version="v0.1.0",
    summary="**A simple interface with the *UCLouvainDown* backend!**",
    # Do not descend the following line after the """ down, it will break openapi
    description="""This API provides an interface with the *UCLouvainDown* backend, allowing to check if services of the 
    University of Louvain (UCLouvain), as well as some other services often used by its students, are up and running 
    (or not).
    </br>
    <ul>
      <li>Non-developpers might be better of using the [UCLouvainDown website](/) rather than passing by this API. It
        is a graphic representation of the same data.</li>
      <li>A webhook interface is also provided, please refer to [the webhook section](/api/docs#tag/Webhooks) of the 
        documentation for the details.</li>
    </ul>
    An issue or request? Please let us know [over on github](https://github.com/Tfloow/UCLouvainDown).
    """,
    docs_url=None,
    redoc_url="/api/docs",
    # terms_of_service="", TODO
    contact={
        "name": "Wouter Vermeulen",
        "email": "wouter.vermeulen@student.uclouvain.be",
    },
    # license_info={}, TODO
)

# Define common responses
api_unkown_url_response = JSONResponse(
    content={"detail": "Sorry, could not find that URL. Please check the documentation at '/api/docs'!"},
    status_code=404
)
api_unkown_service_response = JSONResponse(
    content={"detail": "The requested service is not tracked by this application. Pleasy verify the listed "
                       "services at '/api/services/overview'!"},
    status_code=404
)
webhook_400_response = JSONResponse(
    content={"detail": "One or more of the services listed as those to track, aren't tracked by the application. "
                       "Pleasy verify the listed services at '/api/services/overview'."},
    status_code=400)
webhook_403_response = JSONResponse(
    content={"detail": "The given password does not correspond to the one given when creating the webhook. If entered "
                       "manually, please verify you made no typo."},
    status_code=403)
webhook_404_response = JSONResponse(
    content={"detail": "The webhook for which modifications were asked can't be found."},
    status_code=404)


# FastAPI routes
@api.get(
    "/api/services/overview",
    response_model=List[str],
    responses={
        "200": {"content": {"application/json": {"schema": {"examples": [["Inginious", "ADE-scheduler"]]}}}}
    }
)
def services_overview():
    """
    Get a list of the names of all services that are tracked (that is, regularly checked on their status) by this
    application. This are the only names accepted in requests requiring a service name, such as for example
    [`service_details`](/api/docs#operation/service_details).
    """
    return services.names()


@api.get(
    "/api/services/up/all",
    response_model=Dict[str, bool],
    responses={"200": {"content": {"application/json": {"schema": {"examples": [
        {"Inginious": True, "ADE-scheduler": False}]}}}}
    }
)
def all_service_statuses():
    """
    Get the current status (up or down) for all tracked services. The keys in the response are the name of a
    tracked service, values are booleans: `true` means the service is up and running, `false` means it is down.

    **Note**: *for most applications, the status for only a few services are needed. Please use the
      [`Service Status` endpoint](/api/docs#operation/service_status) instead in those cases!*

    **Note**: *a status change might be reported with a small delay. Applications requiring 100% up-to-date
    information that wish the verify when the status was last checked, should use the
     [`All Service Details` endpoint](/api/docs#operation/all_service_details) or the
     [`Service Details` endpoint](/api/docs#operation/service_details).*
    """
    services.status_changed()
    return {service.name: service.is_up for service in services.root}


@api.get(
    "/api/services/up/{service:str}",
    response_model=bool,
    responses={
        "200": {"content": {"application/json": {"schema": {"title": None}}}},
        "404": {"detail": "Service not tracked", "model": HTTPError}
    }
)
def service_status(
        service: Annotated[
            str,
            Path(
                description="The service for which to get the status. It must be in the list of tracked services"
                            "that can be requested at [this endpoint](/api/docs#operation/services_overview).")
        ]
):
    """
    Get the status of a specific service: `true` if the service is up and running, `false` if it is down.

    **Note**: *a status change might be reported with a small delay. Applications requiring 100% up-to-date
    information that wish the verify when the status was last checked, should use the
     [`Service Details` endpoint](/api/docs#operation/service_details).*

    \f

    Service shall be a valid service, werkzeug already checks this for us with the enumeration of supported services.
    """
    if service not in services.names():
        return api_unkown_service_response

    services.status_changed(service)
    return services.get_service(service).is_up


@api.get(
    "/api/services/all",
    response_model=Services
)
def all_service_details():
    """
    Get the following information on all tracked services:
      * The service url.
      * The current status of the service: is the service up or down (a status change might be reported with a small
        delay - for applications requiring 100% up-to-date information be sure to verify that the `last_checked` field
        in the response is recent enough).
      * The last time the status of the service was checked.

    **Note**: *for most applications, the details for only a few services are needed. Please use the
      [`service details endpoint`](/api/docs#operation/service_details) instead in those cases!*
    """
    services.status_changed()
    return services


@api.get(
    "/api/services/{service:str}",
    response_model=Service,
    responses={
        "404": {"detail": "Service not tracked", "model": HTTPError}
    }
)
def service_details(
        service: Annotated[
            str,
            Path(
                description="The service for which to get the information. It must be in the list of tracked services"
                            "that can be requested at [this endpoint](/api/docs#operation/services_overview).")
        ]
):
    """
    Get the following information on a service by passing its name:
      * The service url.
      * The current status of the service: is the service up or down (a status change might be reported with a small
        delay - for applications requiring 100% up-to-date information be sure to verify that the `last_checked` field
        in the response is recent enough).
      * The last time the status of the service was checked.

    **Note:** *a list of all tracked services can be found at [this endpoint](/api/docs#operation/services_overview).*

    \f

    Service shall be a valid service, werkzeug already checks this for us with the enumeration of supported services.
    """
    if service not in services.names():
        return api_unkown_service_response

    services.status_changed(service)
    return services.get_service(service)


# Purely for the openapi documentation for the webhook callbacks: create an APIRouter
webhook_callback_router = APIRouter()


@webhook_callback_router.post("{$callback_url}", responses=None)
def status_change_notification(_: ServiceStatusChange):
    """
    Receive the information that one of the services had a status change: it went from UP to DOWN or from DOWN to
    UP recently.

    \f

    NO IMPLEMENTATION NECESSARY: this is strictly to get the callback documentation in the openapi specs.
    """
    pass


@api.post(
    "/api/webhooks",
    response_model=WebhookResponse,
    status_code=201,
    tags=["Webhooks"],
    responses={
        "400": {"model": HTTPError, "description": "Unkown service tracking requested"}
    },
    callbacks=webhook_callback_router.routes
)
def create_webhook(
        webhook: Webhook,
        password: Annotated[
            str, Body(
                description="A password associated with the webhook, needed to update or delete it later.")
        ]
):
    """
    Create a webhook to receive updates if the status of one of the requested tracked sites changes.
    """
    for service in webhook.tracked_services:
        if service not in services.names():
            return webhook_400_response
    if not webhook.tracked_services:  # Empty list
        webhook.tracked_services = services.names()

    return webhooks.add_webhook(webhook, password=password)


@api.patch(
    "/api/webhooks/{hook_id:int}",
    response_model=WebhookResponse,
    tags=["Webhooks"],
    responses={
        "400": {"model": HTTPError, "description": "Unkown service tracking requested"},
        "403": {"model": HTTPError, "description": "Wrong password"},
        "404": {"model": HTTPError, "description": "Webhook id unkown"}},
    callbacks=webhook_callback_router.routes
)
def update_webhook(
        hook_id: Annotated[int, Path(description="The id of the webhook to update.")],
        webhook_patches: WebhookPatches,
        password: Annotated[str, Body(
            description="A password associated with the webhook, must be the same as the one given when creating "
                        "the webhook.")
        ]
):
    """
    Update a created webhook to track other services, or to change the callback url.
    """
    if not webhooks.hook_id_exists(hook_id):
        return webhook_404_response
    if not verify_password(webhooks.get_password_hash(hook_id), password):
        return webhook_403_response

    if webhook_patches.tracked_services is not None:
        for service in webhook_patches.tracked_services:
            if service not in services.names():
                return webhook_400_response
        if not webhook_patches.tracked_services:  # Empty list
            webhook_patches.tracked_services = services.names()

    return webhooks.update_webhook(hook_id, webhook_patches)


@hide_422
@api.delete(
    "/api/webhooks/{hook_id:int}",
    status_code=204,
    tags=["Webhooks"],
    responses={
        "403": {"model": HTTPError, "description": "Wrong password"},
        "404": {"model": HTTPError, "description": "Webhook id unkown"}
    }
)
def delete_webhook(
        hook_id: Annotated[int, Path(description="The id of the webhook to delete.")],
        password: Annotated[str, Body(
            description="A password associated with the webhook, must be the same as the one given when creating "
                        "the webhook.")
        ]
):
    """
    Delete a created webhook. No more callbacks will be made based on its content.
    """
    if not webhooks.hook_id_exists(hook_id):
        return webhook_404_response
    if not verify_password(webhooks.get_password_hash(hook_id), password):
        return webhook_403_response

    webhooks.delete_webhook(hook_id)


# Add FastAPI error handling ###########################################################################################
@api.api_route("/api", status_code=404, include_in_schema=False, methods=ALL_HTTP_METHODS)
def api_request_not_found() -> JSONResponse:
    """
    Any paths with `/api` and `/api/...` that have not been catched before are invalid.
    If this endpoint wasn't added, the client would recieve the 404 HTML site from the UCLouvainDown website.
    """
    return api_unkown_url_response


@api.api_route("/api/{_:path}", status_code=404, include_in_schema=False, methods=ALL_HTTP_METHODS)
def api_request_not_found_bis(_: str = "") -> JSONResponse:
    """See `api_request_not_found`."""
    return api_request_not_found()


@api.exception_handler(RequestValidationError)
def custom_exception_handler(request_: Request, exc: RequestValidationError):
    """
    If the `hook_id` given in /api/webhooks/{hook_id} requests is incorrect, that should be a 404 response,
    not a 422 pydantic ValidationError response.
    """
    if request_.url.path[:14] == "/api/webhooks/":
        for err in exc.errors():
            if err['loc'][0] == 'path' and err['loc'][1] == 'hook_id':
                return webhook_404_response

    # If no error was catched, just return the 422 error as normal
    return JSONResponse(
        status_code=422,
        content={'detail': exc.errors(), 'body': exc.body},
    )


# Couple the Flask app and the FastAPI app #############################################################################
api.mount("/", WSGIMiddleware(app))


# Modify the openapi docs a little #####################################################################################
use_route_names_as_operation_ids(api)
hide_default_responses(api)


# Run the whole application ############################################################################################
if __name__ == "__main__":
    uvicorn.run(api)
    # app.run(host="0.0.0.0", debug=True)
