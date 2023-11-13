from rest_framework import status as status_code
from rest_framework.response import Response

from tests.utils import _aut_user, _process_status_codes
from proxy.views.media_permission import REPORT


def __get_response(api_client, model_id: int, object_id: str, user=None, status_codes=None) -> Response:
    """Return response."""
    _aut_user(api_client, user)
    response = api_client.post(f"/api/v1/media-permissions/{REPORT}/{model_id}/{object_id}/")
    scs = _process_status_codes(status_codes, default={status_code.HTTP_200_OK, status_code.HTTP_201_CREATED})

    assert response.status_code in scs, f"response.status_code = {response.status_code}"
    return response
