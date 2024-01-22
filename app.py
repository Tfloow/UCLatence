from flask import Flask, render_template
from models import *


# Load JSON file #######################################################################################################
JSON_FILE = "services.json"
services = Services.load_from_json_file(JSON_FILE)


# Start Flask app ######################################################################################################
app = Flask("UCLouvainDown")


@app.route("/")
def index():
    """Render homepage, with an overview of all services."""
    print(f"[LOG]: HTTP request for homepage")
    services.refresh_status()
    return render_template("index.html", serviceList=services)


@app.route(f"/<any({services.names()}):service>")
def service_details(service: str):
    """Render a page with details of one service."""
    print(f"[LOG]: HTTP request for {service}")
    services.refresh_status(service)
    service_object = services.get_site(service)
    
    return render_template("itemWebsite.html", service=service_object)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
