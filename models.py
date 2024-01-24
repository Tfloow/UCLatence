import datetime as dt

from fastapi import Body
from pydantic import BaseModel, Field, ValidationError, RootModel, HttpUrl
import requests
from typing import List, Dict, Annotated, Optional, Set

from utilities import hash_password

RECHECK_AFTER = 300  # [s]
# Follow ISO guidelines
# DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


# Response-only models #################################################################################################
class HTTPError(BaseModel):
    detail: Annotated[
        str,
        Field(description="Details on the type of error, the reasons why it was raised and/or how to solve it.")
    ]


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

    def callback(self, service):  # : Service):
        if service.name in self.tracked_services:
            requests.post(self.callback_url, json=service.model_dump(mode="json", exclude=["last_checked"]))
            return True

        return False


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


# TODO check if needs to inherit from Service ?
class ServiceStatusChange(BaseModel):
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

    @classmethod
    def load_from_json_file(cls, filename: str):
        try:
            with open(filename, "r") as f:
                return cls.model_validate_json(f.read()).__add_private_vars(filename)
        except OSError | IOError:
            raise Exception("[LOG]: Error when opening/reading webhooks.json")
        except ValueError | ValidationError:
            raise Exception("[LOG]: Error when parsing webhooks.json")

    def dump_json(self, filename: str = None):
        if not filename:
            filename = self.__filename

        try:
            with open(filename, "w") as f:
                f.write(self.model_dump_json(indent=2))
        except OSError | IOError:
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
            raise Exception("Either password or password_hash must be given.")

        self.root.append(hook)
        self.__webhook_dict[hook.hook_id] = hook

        self.dump_json()
        return webhook_response

    def update_webhook(self, hook_id: int, updates: WebhookPatches):
        """Supposes hook_id exists"""
        if updates.callback_url:
            self.__webhook_dict[hook_id].callback_url = updates.callback_url

        if updates.tracked_services:
            old_webhook = self.__webhook_dict[hook_id]
            self.delete_webhook(hook_id)
            return self.add_webhook(
                Webhook(callback_url=old_webhook.callback_url, tracked_services=updates.tracked_services),
                password_hash=old_webhook.password_hash, hook_id=hook_id)

        self.dump_json()
        return WebhookResponse(**self.__webhook_dict[hook_id].model_dump(exclude={"password_hash"}))

    def delete_webhook(self, hook_id: int):
        """Supposes hook_id exists"""
        webhook = self.__webhook_dict.pop(hook_id)
        self.root.remove(webhook)

        self.dump_json()

    def __add_private_vars(self, filename: str):
        for webhook in self.root:
            self.__webhook_dict[webhook.hook_id] = webhook
            if webhook.hook_id > self.__max_id:
                self.__max_id = webhook.hook_id

        self.__filename = filename
        return self

    def callback(self, service) -> int:  # : Service):
        """
        Execute callbacks to webhooks that requested the tracking of `service`.
        This method must be called only if the status of the service juste changed!

        :param service: the service of which the status changed
        :return: the number of successful callbacks made
        """
        counter = 0
        for webhook in self.root:
            counter += webhook.callback(service)
        return counter


class Service(BaseModel):
    name: Annotated[str, Field(
        description="The name by which the service is referenced.",
        examples=["Inginious", "ADE-Scheduler"])]
    url: Annotated[str, Field(
        description="The link to the service.",
        examples=["https://inginious.info.ucl.ac.be/", "https://ade-scheduler.info.ucl.ac.be/calendar"])]
    is_up: Annotated[bool, Field(
        description="The current state of the service: `true` if it is up and running, `false` if it is down.",
        examples=[True, False])]
    last_checked: Annotated[dt.datetime, Field(
        description="The date and time (UTC) at which the status of the service was last checked, in ISO formatting "
                    "(`yyyy-MM-dd'T'HH:mm:ss.SSSXXX`).", examples=["2024-01-22T17:46:55.480345"])]

    __webhooks: List[Webhook] = None

    def status_changed(self) -> bool:
        """
        Refresh the status for this service if not updated recently. Makes an HTTP request to do so.
        Returns True if refresh was necessary and yielded a different result, False if not.

        If a webhooks list is provided, and if the state of the service changed, send out POST requests to each
        webhook in
        """
        now = dt.datetime.utcnow()
        if (now - self.last_checked).total_seconds() > RECHECK_AFTER:
            was_up = self.is_up
            self.is_up = requests.get(self.url).status_code < 400
            self.last_checked = now
            if self.is_up != was_up:
                for webhook in self.__webhooks:
                    webhook.send_callback(self)
                return True

        return False

    @property
    def get_is_up(self):
        self.status_changed()
        return self.is_up


class Services(RootModel):
    root: List[Service]

    __services_dict: Dict[str, Service] = None
    __filename: str = None
    __webhooks: Webhooks = None

    def status_changed(self, service: str | Service = None):
        """Refresh the status for all monitored services (if not updated recently).
        If there are differences, update the json file."""
        if not service:
            [self.status_changed(service) for service in self.root]
        else:
            if isinstance(service, str):
                service = self.__services_dict[service]
            if service.status_changed():
                self.__webhooks.callback(service)

        self.dump_json()

    def names(self) -> List[str]:
        """Get a list of names of all monitored services."""
        return [*self.__services_dict.keys()]

    def get_service(self, service: str) -> Service | None:
        """Get a service from the list, or None if it isn't monitored."""
        return self.__services_dict.get(service, None)

    @classmethod
    def load_from_json_file(cls, filename: str, webhooks: Webhooks = None):
        try:
            with open(filename, "r") as f:
                return cls.model_validate_json(f.read()).__add_private_vars(filename, webhooks)
        except OSError | IOError:
            raise Exception("[LOG]: Error when opening/reading services.json")
        except ValueError | ValidationError:
            raise Exception("[LOG]: Error when parsing services.json")

    def dump_json(self, filename: str = None):
        if not filename:
            filename = self.__filename

        try:
            with open(filename, "w") as f:
                f.write(self.model_dump_json(indent=2))
        except OSError | IOError:
            raise Exception("[LOG]: Error when writing services.json")

    def __add_private_vars(self, filename: str, webhooks: Webhooks):
        self.__services_dict = {service.name: service for service in self.root}
        self.__filename = filename
        self.__webhooks = webhooks
        return self

