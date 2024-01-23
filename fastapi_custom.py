""""""
from typing import Callable

from fastapi import FastAPI
from fastapi.routing import APIRoute


def use_route_names_as_operation_ids(app: FastAPI) -> None:
    """
    Simplify operation IDs so that generated API clients have simpler function
    names.

    Should be called only after all routes have been added.

    Author: Wouter Vermeulen 2024-01-19
    Source: https://fastapi.tiangolo.com/advanced/path-operation-advanced-configuration/#using-the-path-operation-function-name-as-the-operationid
    """
    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name


########################################################################################################################

def hide_422(func: Callable) -> Callable:
    """Parsing error from pydantic
    Author: Wouter Vermeulen 2024-01-19"""
    func.__hide_422__ = True
    return func


def hide_default_responses(app: FastAPI) -> None:
    """
    Hide the responses as indicated with the decorators above.

    Slighly based on [this github comment](https://github.com/tiangolo/fastapi/issues/497#issuecomment-546752110).

    Author: Wouter Vermeulen 2024-01-19
    """

    def delete_response(route, paths, response: str):
        methods = route.methods or ["GET"]
        for method in methods:
            try:
                paths[route.path][method.lower()]["responses"].pop(response)
            except KeyError:
                pass

    openapi_schema = app.openapi()

    paths = openapi_schema["paths"]
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue

        for response_status_code in [422]:
            if getattr(route.endpoint, f"__hide_{response_status_code}__", None):
                delete_response(route, paths, str(response_status_code))

