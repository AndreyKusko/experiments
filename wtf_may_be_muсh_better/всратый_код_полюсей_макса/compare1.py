from rest_framework.status import HTTP_200_OK, HTTP_403_FORBIDDEN
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from clients.policies.actions import METHOD_ACTIONS_MAP, ACTION_TARGET_GROUP, PolicyTargets
from ma_saas.constants.system import GET, POST, DELETE
from ma_saas.constants.company import CUR
from clients.policies.interface import PoliciesServ
from companies.models.company_user import CompanyUser


def get_user_permissions(user_id, company_id, method):
    """
        Получение маппинга с доступом юзера к изменению полюсей
    """
    return {
        PolicyTargets.USER_POLICY: PoliciesServ().has_object_policy(
            user_id=user_id,
            action_target=PolicyTargets.USER_POLICY,
            action_type=METHOD_ACTIONS_MAP[method],
            obj_id=company_id,
            obj_type=PolicyTargets.COMPANY,
        ),
        PolicyTargets.PROJECT_POLICY: PoliciesServ().has_object_policy(
            user_id=user_id,
            action_target=PolicyTargets.PROJECT_POLICY,
            action_type=METHOD_ACTIONS_MAP[method],
            obj_id=company_id,
            obj_type=PolicyTargets.COMPANY,
        ),
        PolicyTargets.BILLING_POLICY: PoliciesServ().has_object_policy(
            user_id=user_id,
            action_target=PolicyTargets.BILLING_POLICY,
            action_type=METHOD_ACTIONS_MAP[method],
            obj_id=company_id,
            obj_type=PolicyTargets.COMPANY,
        ),
    }


def can_change_policy(policy, requested_user, request_user_permissions):
    """
        Проверяем, может ли юзер изменить переданный полиси
    """
    # если нет базового права, ничего не проверяем
    if not request_user_permissions[PolicyTargets.USER_POLICY]:
        return False

    redis = PoliciesServ().redis
    action_id = None

    if "action" not in policy and "action_id" not in policy:
        return False

    if "action" in policy:
        action_id = policy["action"]["id"]
    if "action_id" in policy:
        action_id = policy["action_id"]

    action_data = redis.get(f"policy_actions.{action_id}")

    if action_data:
        action_target, action_type = action_data.decode("utf-8").split(".")

        if action_target in ACTION_TARGET_GROUP:
            permission_policy = ACTION_TARGET_GROUP[action_target]
            if not request_user_permissions[permission_policy]:
                return False

        if "scope_id" not in policy or not policy["scope_id"]:
            can_change = True
            for policy_obj in policy["policy_objects"]:
                if not PoliciesServ().has_object_policy(
                    requested_user, action_target, action_type, action_target, policy_obj["obj_id"]
                ):
                    can_change = False
                    break
            return can_change
        else:
            return PoliciesServ().has_object_policy(
                requested_user, action_target, action_type, policy["scope_type"], policy["scope_id"]
            )


@api_view([GET, DELETE, POST])
@permission_classes([IsAuthenticated])
def policies_permissions(request):
    """
        Это право используется для взаимодействия с полисисервом, кроме чтения/записи/удаления полюсей.
    """
    if request.query_params.get("method") != "GET":
        return Response(status=HTTP_403_FORBIDDEN)
    else:
        return Response(status=HTTP_200_OK)


@api_view([GET])
@permission_classes([IsAuthenticated])
def policiesserv_actions(request):
    """
        Получение списка экшенов, проксируется для сохранения в редис текущего списка
    """
    resp = PoliciesServ().get_actions()

    redis = PoliciesServ().redis
    for action in resp:
        redis.set(f"policy_actions.{action['id']}", f'{action["target"]}.{action["action_type"]}')

    return Response(status=HTTP_200_OK, data=resp)


@api_view([GET])
@permission_classes([IsAuthenticated])
def policiesserv_roles(request):
    """
        Получение ролей
    """
    roles = PoliciesServ().get_roles()
    return Response(status=HTTP_200_OK, data=roles)


@api_view([GET, POST])
@permission_classes([IsAuthenticated])
def policiesserv_policies(request):
    """
        Проверяем права на чтение полиси юзера
        Проверяем права юзера на запись переданных полиси и записываем если все ок

        Пример зпроса полюсей для пользователя
        curl --location --request GET 'https://dev.ma.direct/api/policiesserv/policies/' --header 'Accept: application/json' --header 'Authorization: Token dd8e1bd4f2e7d5fdcb501670030827958e6ab8c6' --header 'Cookie: csrftoken=nyF1e1cQMA7Rr8QVE2hLbZa1IH8g0sstron5vU8S5DFld9xrA544KK8tLkisW06U' --header 'X-USER-ID: 16'
    """
    company_id = request.META.get("X-COMPANY-ID", None) or request.META.get("HTTP_X_COMPANY_ID", None)
    changeable_user = request.META.get("X-USER-ID", None) or request.META.get("HTTP_X_USER_ID", None)

    requested_user = request.user.id
    request_user_permissions = get_user_permissions(requested_user, company_id, request.method)

    # Проверка прав на чтение
    if request.method == GET:
        can_read = False
        # Собственные права юзер может читать всегда
        if not changeable_user or int(changeable_user) == requested_user:
            can_read = True
        # Проверяем доступ на чтение чужих прав
        elif changeable_user and int(changeable_user) != requested_user:
            can_read = request_user_permissions[PolicyTargets.USER_POLICY]

            # Проверяем принадлежность юзера права которого читаем, к нужной компании
            try:
                user = CompanyUser.objects.get(
                    user_id=changeable_user, company_id=company_id, is_deleted=False
                )
            except CompanyUser.DoesNotExist:
                can_read = False

        if can_read:
            resp = PoliciesServ().get_policies(changeable_user)
            return Response(status=HTTP_200_OK, data=resp)
        else:
            return Response(status=HTTP_403_FORBIDDEN)

    # Проверка прав на запись полюсей
    if request.method == POST:
        changeable_user = request.data.get("user_id")
        struct = request.data.get("struct")

        is_owner = False
        # Проверяем, является ли изменяющий права юзер овнером
        try:
            user = CompanyUser.objects.get(
                user_id=requested_user, company_id=company_id, is_deleted=False, role=CUR.OWNER
            )
            if user:
                is_owner = True
        except CompanyUser.DoesNotExist:
            pass

        # Свои права менять может только овнер
        if int(changeable_user) == requested_user and not is_owner:
            return Response(status=HTTP_403_FORBIDDEN)

        can_change = request_user_permissions[PolicyTargets.USER_POLICY]

        if can_change:
            if not is_owner:
                # Проверяем, что изменяемый юзер принадлежит к переданной компании
                try:
                    CompanyUser.objects.get(user_id=changeable_user, company_id=company_id, is_deleted=False)
                except CompanyUser.DoesNotExist:
                    return Response(status=HTTP_403_FORBIDDEN)

                # Проверяем все переданные полиси
                for policy in struct:
                    if not can_change_policy(policy, requested_user, request_user_permissions):
                        return Response(status=HTTP_403_FORBIDDEN)

            resp = PoliciesServ().write_policies(changeable_user, struct, False)
            return Response(status=HTTP_200_OK, data=resp)

    return Response(status=HTTP_403_FORBIDDEN)


@api_view([DELETE])
@permission_classes([IsAuthenticated])
def delete_policy(request, policy_id):
    """
        Проверяем права на чтение полиси юзера
        Проверяем права юзера на запись переданных полиси и записываем если все ок
    """
    company_id = request.META.get("X-COMPANY-ID", None) or request.META.get("HTTP_X_COMPANY_ID", None)
    requested_user = request.user.id
    request_user_permissions = get_user_permissions(requested_user, company_id, request.method)

    policy = PoliciesServ().fetch_policy(policy_id)
    if policy and len(policy) > 0:
        policy = policy[0]

        is_owner = False
        # Проверяем, является ли изменяющий права юзер овнером
        try:
            user = CompanyUser.objects.get(
                user_id=requested_user, company_id=company_id, is_deleted=False, role=CUR.OWNER
            )
            if user:
                is_owner = True
        except CompanyUser.DoesNotExist:
            pass

        if policy["user_id"] == requested_user and not is_owner:
            return Response(status=HTTP_403_FORBIDDEN)

        if is_owner or can_change_policy(policy, requested_user, request_user_permissions):
            PoliciesServ().delete_policy(policy["user_id"], policy_id)
            return Response(status=HTTP_200_OK)

    return Response(status=HTTP_403_FORBIDDEN)
