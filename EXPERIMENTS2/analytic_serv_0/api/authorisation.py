from fastapi import Header, HTTPException

from main.settings import ANALYTIC_SERVICE_AUTH_TOKEN
from main.constants import TRUST_KIND


async def check_authorization(Authorization: str = Header(...)):
    splited = Authorization.split(" ")
    if not len(splited) == 2:
        raise HTTPException(status_code=400, detail="Authorization header too short")
    kind, token = splited
    if kind == TRUST_KIND and token == ANALYTIC_SERVICE_AUTH_TOKEN:
        return
    raise HTTPException(status_code=400, detail="Authorization header invalid")
