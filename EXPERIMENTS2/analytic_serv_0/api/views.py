from typing import List, Optional

from fastapi import Depends, Response, APIRouter

from api.authorisation import check_authorization
from api.models import Event
from api.schemas import EventSchema

router = APIRouter(
    prefix="/api/v1",
    tags=["views"],
    dependencies=[Depends(check_authorization)],
    responses={404: {"description": "Not found"}},
)
READ_ONLY_FIELDS = {"company", "id"}


@router.get("/events/", response_model=List[EventSchema])
def list_events(
    company_id: int,
    user_id: int = None,
    project_id: int = None,
    created_at__gte: Optional[str] = None,
    created_at__lte: Optional[str] = None,
):
    """
    Получить список правил нотификации

    В примере курла представлены все параметры, которые могут быть использованы.
    company_id - обязательный параметр

    Пример.

        curl --location --request GET 'http://127.0.0.1:8005/api/v1/notification-rules/?company_id=1&id=1&is_active=true&notification_kinds__contains=email' --header 'Accept: application/json' --header 'Content-Type: application/json' --header 'Authorization: TRUST 123qweasd'
    """
    queryset = Event.objects.filter(company_id=company_id)
    # if id:
    #     queryset = queryset.filter(id=id)
    # if is_active is not None:
    #     queryset = queryset.filter(is_active=is_active)
    # if notification_kinds__contains is not None:
    #     notification_kinds__contains = notification_kinds__contains.split(",")
    #     queryset = queryset.filter(notification_kinds__contains=notification_kinds__contains)
    return EventSchema.from_qs(instances=queryset)
