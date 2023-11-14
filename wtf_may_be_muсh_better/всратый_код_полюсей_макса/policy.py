from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsTotallyActiveUser
from ma_saas.constants.system import GET, POST, DELETE, OPTIONS
from proxy.permissions.policy import IsAllowedToPolicies, retrieve_data
from clients.policies.interface import Policies
from companies.models.company_user import CompanyUser
from proxy.views.policies_serv.main import PolicyServ


class PolicyPoliciesViewsSet(PolicyServ):
    """
    Получение списка полюсей

    При изменении полюсей целевого пользователя
        и несоответствии набора полюсей како-либо роли в полюси серве,
        в сервисе сааса назначится роль на "custom"

    *List:*
    Пример запроса:
        curl --location --request POST 'http://127.0.0.1:8000/api/v1/policy/policies/' --header 'Accept: application/json' --header 'Authorization: Token 4ec818791b436f5e68da10ba77415b63a485b30b' --form 'company_id="3"' --form 'user_id="319824"' --form 'struct="[{\"id\":3743,\"scope_type\":\"company\",\"scope_id\":3,\"action\":{\"id\":76}, \"_destroy\":true}]"'
    Пример выдачи:
        [{"id": 3746, "action": {"id": 76, "title": "user_policy read", "description": {"title": "user_policy"}, "target": "user_policy", "action_type": "read"}, "scope_id": 3, "scope_type": "company", "user_id": 319824, "policy_objects": [], "is_active": true}, ...]

    *Create*
    Пример запроса:
        curl --location --request GET 'http://127.0.0.1:8000/api/v1/policy/policies/?company_id=3&user_id=319824' --header 'Accept: application/json' --header 'Authorization: Token 4ec818791b436f5e68da10ba77415b63a485b30b'
    Пример выдачи:
        [{"id": 3746, "action": {"id": 76, "title": "user_policy read", "description": {"title": "user_policy"}, "target": "user_policy", "action_type": "read"}, "scope_id": 3, "scope_type": "company", "user_id": 319824, "policy_objects": [], "is_active": true}, ...]

    *Delete*
    _Пока требуется посылать query параметры, но в будущем это может не понадобится_
        curl --location --request DELETE 'http://127.0.0.1:8000/api/v1/policy/policies/3746/?company_id=3&user_id=319824' --header 'Accept: application/json' --header 'Authorization: Token 4ec818791b436f5e68da10ba77415b63a485b30b'
    В ответ ничего не приходит, код ответа 204
    """

    allowed_methods = [GET, POST, DELETE, OPTIONS]
    permission_classes = (IsAuthenticated & IsTotallyActiveUser & IsAllowedToPolicies,)
    proxy_class = Policies

    def list(self, request, *args, **kwargs):
        target_user_id = int(request.GET.get("user_id", request.user.id))
        self.serv_request.sync_policies(target_user_id, self.serv_request.list(target_user_id))
        instances = self.serv_request.list(target_user_id)
        return Response(status=HTTP_200_OK, data=instances)

    def create(self, request, *args, **kwargs):
        target_company_id, target_user_id, struct = retrieve_data(request)
        struct = request.data.get("struct")
        instances = self.serv_request.write_policies(target_user_id, struct, False)

        target_cu = CompanyUser.objects.get(company_id=target_company_id, user_id=target_user_id)
        target_cu.set_new_role_according_policy_serv()
        return Response(status=HTTP_200_OK, data=instances)

    def destroy(self, request, pk, *args, **kwargs):
        policy_id = int(pk)
        if not (instances := self.serv_request.retrieve(policy_id)):
            raise NotFound("Запрошенная полюся не найдена")
        instance = instances[0]
        self.serv_request.delete(instance["user_id"], policy_id)
        return Response(status=HTTP_204_NO_CONTENT)
