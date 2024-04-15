import datetime as dt

from fastapi import Body
from pydantic import BaseModel, Field, ValidationError, RootModel, HttpUrl, computed_field
import requests
from typing import List, Dict, Annotated, Set, Any, Iterable
from logger_config import *

from utilities import hash_password

import os

# Basic constant
filepath = "data/"
cols = "date,UP\n"
RECHECK_AFTER = 300  # [s]
# Follow ISO guidelines
# DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


webhook_tracked_services = Body(
            description="The services for which to receive updates. An empty list default to all tracked services.",
            examples=[["Inginous", "ADE-scheduler"], []]
        )
webhook_callback_url = Body(
            description="The url to which should be sent the `POST` requests containing updates.",
            examples=["https://somesite/api/webhooks/UCLouvainDownResponses"]
        )


class Webhook(BaseModel):
    tracked_services: Annotated[
        Set[str],
        webhook_tracked_services]
    callback_url: Annotated[
        HttpUrl,
        webhook_callback_url]

    def send_callback(self, service) -> bool:
        """
        Check that this webhook tracks `service` and if so send a callback to the callback_url.

        :returns: `True if a callback was sent, `False` if not.
        """
        if service.name in self.tracked_services:
            requests.post(self.callback_url, json=service.model_dump(mode="json", exclude=["last_checked"]))
            return True

        return False


# Response-only models #################################################################################################
class HTTPError(BaseModel):
    detail: Annotated[
        str,
        Field(description="Details on the type of error, the reasons why it was raised and/or how to solve it.")
    ]


class WebhookPatches(Webhook):
    """The updates to be made to the webhook."""
    tracked_services: Annotated[List[str], webhook_tracked_services] = None
    callback_url: Annotated[str, webhook_callback_url] = None


class WebhookResponse(Webhook):
    hook_id: Annotated[
        int,
        Field(
            description="The id of the webhook, to be used in the future for `PATCH` or `DELETE` requests.",
            examples=[123, 1])]


class WebhookComplete(WebhookResponse):
    """\f this class shall never be used as a return type on an api call!!!"""
    password_hash: str

    def __eq__(self, other):
        return isinstance(other, WebhookComplete) and self.hook_id == other.hook_id


# TODO check if needs to inherit from Service ?
class ServiceStatusChange(BaseModel):
    # Model for API callbacks
    name: Annotated[str, Field(
        description="The name by which the service is referenced.",
        examples=["Inginious", "ADE-Scheduler"])]
    url: Annotated[str, Field(
        description="The link to the service.",
        examples=["https://inginious.info.ucl.ac.be/", "https://ade-scheduler.info.ucl.ac.be/calendar"])]
    is_up: Annotated[bool, Field(
        description="The current state of the service: `true` if it is up and running, `false` if it is down. "
                    "If it was down before, its state now will be `true` and inversely.",
        examples=[True, False])]


# Models used for backend ##############################################################################################


class Webhooks(RootModel):
    root: List[WebhookComplete]

    __webhook_dict: Dict[int, WebhookComplete] = {}
    __filename: str = None
    __max_id: int = 0
    __services = None

    @classmethod
    def load_from_json_file(cls, filename: str):
        try:
            with open(filename, "r") as f:
                return cls.model_validate_json(f.read()).__post_init(filename)
        except (OSError, IOError):
            raise Exception("[LOG]: Error when opening/reading webhooks.json")
        except (ValueError, ValidationError):
            raise Exception("[LOG]: Error when parsing webhooks.json")

    def dump_json(self, filename: str = None):
        if not filename:
            filename = self.__filename

        try:
            with open(filename, "w") as f:
                f.write(self.model_dump_json(indent=2))
        except (OSError, IOError):
            raise Exception("[LOG]: Error when writing webhooks.json")

    def hook_id_exists(self, hook_id: int) -> bool:
        return hook_id in self.__webhook_dict

    def get_password_hash(self, hook_id: int):
        """Supposes hook_id exists"""
        return self.__webhook_dict[hook_id].password_hash

    def add_webhook(self, webhook: Webhook, password: str = None, password_hash: str = None,
                    hook_id: int = None) -> WebhookResponse:
        if not hook_id:
            self.__max_id += 1
            hook_id = self.__max_id
        webhook_response = WebhookResponse(**webhook.model_dump(), hook_id=hook_id)
        if password:
            hook = WebhookComplete(**webhook_response.model_dump(), password_hash=hash_password(password))
        elif password_hash:
            hook = WebhookComplete(**webhook_response.model_dump(), password_hash=password_hash)
        else:
            raise AttributeError("Either password or password_hash must be given.")

        self.root.append(hook)
        self.__webhook_dict[hook.hook_id] = hook

        if services:
            for service in services:
                service.modify_webhooks([hook])

        self.dump_json()
        return webhook_response

    def update_webhook(self, hook_id: int, updates: WebhookPatches):
        """Supposes hook_id exists"""
        self.__webhook_dict[hook_id].callback_url = updates.callback_url or self.__webhook_dict[hook_id].callback_url

        if updates.tracked_services:  # is not None
            # Not the most efficient but works
            old_webhook = self.__webhook_dict[hook_id]
            self.delete_webhook(hook_id)
            return self.add_webhook(
                WebhookComplete(callback_url=old_webhook.callback_url, tracked_services=updates.tracked_services,
                password_hash=old_webhook.password_hash, hook_id=hook_id))

        self.dump_json()
        return WebhookResponse(**self.__webhook_dict[hook_id].model_dump(exclude={"password_hash"}))

    def delete_webhook(self, hook_id: int):
        """Supposes hook_id exists"""
        webhook = self.__webhook_dict.pop(hook_id)
        self.root.remove(webhook)
        webhook.tracked_services = set()
        if services:
            for service in services:
                service.modify_webhooks([webhook])
        self.dump_json()

    def _set_services(self, services): # Services
        self.__services = services

    def __post_init(self, filename: str):
        for webhook in self.root:
            self.__webhook_dict[webhook.hook_id] = webhook
            if webhook.hook_id > self.__max_id:
                self.__max_id = webhook.hook_id

        self.__filename = filename
        return self

    def __iter__(self) -> Iterable[WebhookComplete]:
        return iter(self.root)


class Service(BaseModel):
    name: Annotated[str, Field(
        description="The name by which the service is referenced.",
        examples=["Inginious", "ADE-Scheduler"])]
    url: Annotated[str, Field(
        description="The link to the service.",
        examples=["https://inginious.info.ucl.ac.be/", "https://ade-scheduler.info.ucl.ac.be/calendar"])]
    status: Annotated[bool, Field(
        description="The current status of the service: `true` if it is up and running, `false` if it is down.",
        examples=[True, False], alias="is_up", alias_priority=1)]
    last_checked: Annotated[dt.datetime, Field(
        description="The date and time (UTC) at which the status of the service was last checked, in ISO formatting "
                    "(`yyyy-MM-dd'T'HH:mm:ss.SSSXXX`).", examples=["2024-01-22T17:46:55.480345"])]
    is_up_user: Annotated[bool, Field(
        description="The current status of the service according to the latest user report. Check `last_user_status`"
                    "for the date and time at which this status was reported.", examples=[True, False]
    )]
    last_user_report: Annotated[dt.datetime, Field(
        description="The date and time (UTC) at which the last user reported the status of this service, in ISO"
                    "formatting (`yyyy-MM-dd'T'HH:mm:ss.SSSXXX`).", examples=["2024-01-22T17:46:55.480345"]
    )]

    __webhooks: Dict[int, Webhook] = {}
    __parent: None  # Services instance

    def status_changed(self, session=None):
        """
        Refresh the status for this service if not updated recently. Makes an HTTP request to do so. This method
        can trigger a callback to all associated webhooks if the status did change.
        
        :param session: a https session to speed up checks (because it can use batch requests)
        """
        now = dt.datetime.utcnow()
        headers = {"User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) "
                                 "Chrome/81.0.4044.141 Safari/537.36",
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"}

        if self.status is None or True: #(now - self.last_checked).total_seconds() > RECHECK_AFTER: maybe this was the cause of the duplication bug
            try:
                if session is None:
                    new_is_up = requests.head(self.url, headers=headers, timeout=60, allow_redirects=True).status_code < 400
                else:
                    new_is_up = session.head(self.url, headers=headers).status_code < 400
                self.last_checked = now

                if self.status is None:
                    self.status = new_is_up
                elif self.status != new_is_up:
                    for webhook in self.__webhooks.values():
                        webhook.send_callback(self)
                    self.status = new_is_up
            except Exception as error:
                logger.warning(f"[LOG]: Error {error}")
                logger.info(f"[LOG]: Error when checking the status of {self.name}")
                new_is_up = False
                self.last_checked = now

        self.__parent.dump_json()

    @property
    def is_up(self) -> bool:
        """
        Updates the value of `is_up` if necessary then returns it.
        If value changes `is_up`, calls all webhooks associated with the service to
        notify them of the status change.
        :return: `true` if the service is up, `false if not` (this value isn't 100% accurate: status checks don't
          happen every second).
        """
        # self.status_changed() Because the update of the status should only be done periodically
        return self.status

    def modify_webhooks(self, webhooks: List[WebhookComplete]):
        """
        Add the webhooks given in `webhooks` if those requested the tracking of this service, or delete them if they
        were tracking this service before but now not anymore.
        """
        for webhook in webhooks:
            # Check if the webhook should be deleted
            if webhook.hook_id in self.__webhooks and self.name not in webhook.tracked_services:
                self.__webhooks.pop(webhook.hook_id, None)
            # Or add the webhook
            elif self.name in webhook.tracked_services:
                self.__webhooks[webhook.hook_id] = webhook

    def _set_parent(self, parent):
        self.__parent = parent


class Services(RootModel):
    root: Dict[str, Service]

    __tracked_services: Set[str] = None  # Keyset from the root dict (going from KeyView to Set is O(n))
    __filename: str = None

    @classmethod
    def load_from_json_file(cls, filename: str, webhooks: Webhooks = None):
        """
        Load a `Services` object from a json file. The file should have the following structure::

            {
                str: {
                    "name": str,
                    "url": str,
                    "is_up": bool,
                    "last_checked": str,  # Should be a datetime in ISO format
                }
            }

        :param filename: the name of the file from which to load the object. By default, the object will save any
          changes to itself again to that file.
        :param webhooks: the webhooks to associate with the object
        :return: a `Services` object containing all information from the json file
        """
        try:
            with open(filename, "r") as f:
                return cls.model_validate_json(f.read()).__post_init(filename, webhooks)
        except (OSError, IOError):
            raise Exception("[LOG]: Error when opening/reading services.json")
        except (ValueError, ValidationError):
            raise Exception("[LOG]: Error when parsing services.json")

    def dump_json(self, filename: str = None):
        """
        Write the object again to a json file.

        :param filename: the file to which the object should be written. If not specified, the file from which the
          object was read is overwritten.
        """
        if not filename:
            filename = self.__filename

        try:
            with open(filename, "w") as f:
                f.write(self.model_dump_json(indent=2, by_alias=True))
        except (OSError, IOError):
            raise Exception("[LOG]: Error when writing services.json")

    def status_changed(self, service: str | Service = None):
        """Refresh the status for all monitored services (if not updated recently).
        If there are differences, update the json file."""
        if not service:
            [self.status_changed(service) for service in self.root.values()]
        else:
            if isinstance(service, str):
                service = self.root[service]
            service.status_changed()

        self.dump_json()

    def get_service(self, service_name: str) -> Service | None:
        """Get a service from the list, or None if it isn't monitored."""
        return self.root.get(service_name, None)

    def add_service(self, name: str, url: str):
        """
        Add a new service to the list of services (it will be added to the json file from which the object was loaded).

        :param name: a name for the service (should contain only characters that can be used in urls)
        :param url: a url for the service
        """
        new_service = Service(name=name, url=url, is_up=True, last_checked=dt.datetime.utcnow(),
                              is_up_user=True, last_user_report=dt.datetime.utcnow())
        new_service._set_parent(self)
        self.root[name] = new_service
        self.__tracked_services.add(name)
        
        # For the Data and Logs
        try:
            os.mkdir(filepath + name)
        except FileExistsError:
            pass 
        except Exception as _:
            raise ValueError(f"[LOG]: Something went wrong with creating the folder {name}")
        
        with open(filepath + name + "/log.csv", "w") as log:
            log.write(cols)
            
        with open(filepath + name + "/outageReport.csv", "w") as out:
            out.write(cols)
            
        with open(filepath + name + "/outageReportArchive.csv", "w") as out:
            out.write(cols)
        
        self.dump_json()

    @property
    def names(self) -> Set[str]:
        """Get a set of names of all monitored services."""
        return self.__tracked_services

    def __post_init(self, filename: str, webhooks: Webhooks | None):
        """
        As the pydantic `model_validate_json` only reads what is in the json file, this is a 'post initialisation'
        function to complete the object creation.

        :param filename: the file from which the object was charged. By default, the object will save any changes to
          itself again to that file.
        :param webhooks: the webhooks to associate with the object
        """
        self.__tracked_services = set(self.root.keys())
        self.__filename = filename
        for service in self:
            service._set_parent(self)
        if webhooks:
            for service in self.root.values():
                service.modify_webhooks(webhooks.root)

        return self

    def __contains__(self, item: Any) -> bool:
        if not isinstance(item, str):
            return False
        return item in self.__tracked_services

    def __iter__(self) -> Iterable[Service]:
        """Return an iterator over the the tracked services objects"""
        return self.root.values().__iter__()


if __name__ == "__main__":
    JSON_FILE_WEBHOOKS = "webhooks.json"
    webhooks = Webhooks.load_from_json_file(JSON_FILE_WEBHOOKS)

    JSON_FILE_SERVICES = "services.json"
    services = Services.load_from_json_file(JSON_FILE_SERVICES, webhooks=webhooks)
    
    # services.add_service("IDP-Logging", "https://idp.uclouvain.be")
