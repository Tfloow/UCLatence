from dataclasses import asdict, dataclass
import datetime as dt
import json
import requests
from typing import List


RECHECK_AFTER = 300  # [s]
# Follow ISO guidelines
# DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


@dataclass
class Service:
    name: str
    url: str
    last_status: bool
    last_access_time: dt.datetime | str

    def __post_init__(self):
        # Make sure last_access is an instance of dt.datetime
        if not isinstance(self.last_access_time, dt.datetime):
            self.last_access = dt.datetime.fromisoformat(self.last_access_time)

    def refresh_status(self) -> bool:
        """Refresh the status for this site if not updated recently. Makes an HTTP request to do so."""
        currentDate = dt.datetime.now()
        if (currentDate - self.last_access).total_seconds() > RECHECK_AFTER:
            self.last_status = requests.get(self.url).status_code < 400
            self.last_access_time = dt.datetime.now()

        return self.last_status


class Services:
    def __init__(self, services: List[Service], filename: str):
        self.services = services
        self.services_dict = {site.name: site for site in self.services}

        self.filename = filename

    def refresh_status(self, service: str = None):
        """Refresh the status for all monitored sites (if not updated recently)."""
        if not service:
            [site.refresh_status() for site in self.services]
        else:
            self.services_dict[service].refresh_status()
        self.dump_json()

    def dump_json(self, filename: str = None):
        """Dump the monitored sites back into a json file. If no file is specified, overwrites the file given at
         initialisation."""
        filename = filename if filename else self.filename
        with open(filename, "w") as out:
            json.dump([asdict(service) for service in self.services], out, indent=4, default=str)

    def names(self):
        """Get a list of names of all monitored sites."""
        return self.services_dict.keys()

    def get_site(self, service: str) -> Service | None:
        """Get a site from the list, or None if it isn't monitored."""
        return self.services_dict.get(service, None)

    def __iter__(self):
        return self.services.__iter__()

    @staticmethod
    def load_from_json_file(filename: str):
        """Load a Services instance from a the json file."""
        try:
            f = open(filename, "r")
        except OSError | IOError as _:
            raise ValueError("[LOG]: Error when opening services.json")

        try:
            retval = Services(json.load(f, object_hook=lambda value: Service(**value)), filename)
        except Exception as _:
            raise Exception("[LOG]: Error when parsing services.json")

        f.close()
        return retval
