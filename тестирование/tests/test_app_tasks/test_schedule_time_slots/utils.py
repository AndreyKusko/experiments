from django.forms import model_to_dict

from ma_saas.constants.system import DATETIME_FORMAT
from tasks.models.reservation import Reservation


def compare_response_and_instance(instance: Reservation, data: dict):
    assert data.pop("geo_point_address") == instance.geo_point.address
    assert data.pop("reward") == instance.geo_point.project_territory.reward
    assert data.pop("created_at") == instance.created_at.strftime(DATETIME_FORMAT)
    assert data.pop("updated_at") == instance.updated_at.strftime(DATETIME_FORMAT)
    assert data.pop("first_name") == instance.project_territory_worker.company_user.user.first_name
    assert data.pop("last_name") == instance.project_territory_worker.company_user.user.last_name
    assert data.pop("company_user_id") == instance.project_territory_worker.company_user.id
    instance_dict = model_to_dict(instance)
    assert all(instance_dict[name] == value for name, value in data.items())
    return True
