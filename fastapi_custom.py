""""""

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

