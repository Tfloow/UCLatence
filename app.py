from flask import Flask, render_template
from models import *


# Load JSON file #######################################################################################################
JSON_FILE = "services.json"
services = Services.load_from_json_file(JSON_FILE)


# Start Flask app ######################################################################################################
app = Flask("UCLouvainDown")


@app.route("/")
async def index():
    """Render homepage, with an overview of all services."""
    print(f"[LOG]: HTTP request for homepage")
    print(services)
    await services.refresh_status()
    return render_template("index.html", serviceList=services)


@app.route(f"/<any({services.names()}):service>")
async def service_details(service: str):
    """Render a page with details of one service."""
    print(f"[LOG]: HTTP request for {service}")
    service_object = services.get_site(service)

    await services.refresh_status(service)
    return render_template("itemWebsite.html", service=service_object)


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

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
