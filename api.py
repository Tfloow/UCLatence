from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import Field, BaseModel
import datetime as dt

router = APIRouter()





@router.get("/")
def test():
    """

    :return:
    """
    return JSONResponse(content="All ok", status_code=200)