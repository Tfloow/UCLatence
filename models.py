import datetime as dt
from pydantic import BaseModel, Field, ValidationError, RootModel
import requests
from typing import List, Dict, Set

RECHECK_AFTER = 300  # [s]
# Follow ISO guidelines
# DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


class Service(BaseModel):
    name: str = Field(
        description="The name by which the service is known.",
        examples=["Inginious", "ADE-Scheduler"])
    url: str = Field(
        description="The link to the service.",
        examples=["https://inginious.info.ucl.ac.be/", "https://ade-scheduler.info.ucl.ac.be/calendar"])
    is_up: bool = Field(
        description="The current state of the service: `true` if it is up and running, `false` if it is down.",
        examples=[True])

    last_checked: dt.datetime = Field(
        description="The date and time at which the status of the service was last checked, in ISO formatting "
                    "(`'YYYY'-'MM'-'DD'T'HH':'MM':'SS'.'SSSSS'`).", examples=["2024-01-22T17:46:55.480345"])

    def refresh_status(self) -> bool:
        """Refresh the status for this service if not updated recently. Makes an HTTP request to do so.
        Returns True if refresh was necessary and yielded a different result, False if not."""
        now = dt.datetime.utcnow()
        if (now - self.last_checked).total_seconds() > RECHECK_AFTER:
            was_up = self.is_up
            self.is_up = requests.get(self.url).status_code < 400
            self.last_checked = now
            return self.is_up != was_up

        return False


class Services(RootModel):
    root: List[Service]

    __services_dict: Dict[str, Service] = None
    __filename: str = None

    async def refresh_status(self, service: str = None):
        """Refresh the status for all monitored services (if not updated recently).
        If there are differences, update the json file."""
        if not service:
            [service.refresh_status() for service in self.root]
        else:
            self.__services_dict[service].refresh_status()

        self.dump_json()

    def names(self) -> List[str]:
        """Get a list of names of all monitored services."""
        return [*self.__services_dict.keys()]

    def get_service(self, service: str) -> Service | None:
        """Get a service from the list, or None if it isn't monitored."""
        return self.__services_dict.get(service, None)

    def dump_json(self, filename: str = None):
        if not filename:
            filename = self.__filename
        try:
            with open(filename, "w") as f:
                f.write(self.model_dump_json(indent=2))
        except OSError | IOError:
            raise Exception("[LOG]: Error when writing services.json")

    @classmethod
    def load_from_json_file(cls, filename: str):
        try:
            with open(filename, "r") as f:
                return cls.model_validate_json(f.read()).add_private_vars(filename)
        except OSError | IOError:
            raise Exception("[LOG]: Error when opening/reading services.json")
        except ValueError | ValidationError:
            raise Exception("[LOG]: Error when parsing services.json")

    def add_private_vars(self, filename: str):
        self.__services_dict = {service.name: service for service in self.root}
        self.__filename = filename
        return self
