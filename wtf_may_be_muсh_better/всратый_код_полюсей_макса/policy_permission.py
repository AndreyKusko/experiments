
class IsAllowedToPolicies(permissions.BasePermission):
    def has_permission(self, request, view) -> bool:
        target_company_id, target_user_id, struct = retrieve_data(request=request)
        existing_cus = get_existing_objs_or_403(CompanyUser, company_id=target_company_id)
        r_u = request.user
        target_user = get_obj_or_403(existing_cus, user_id=target_user_id)
        if existing_cus.accepted_owners().filter(user=r_u).exists():
            # овнер может менять и смотреть все полюси
            return True
        if is_dangerous_method(request.method) and target_user.is_owner and r_u.id != target_user_id:
            raise PermissionDenied("Менять роли полиси овнера может только сам овнер")
        if is_dangerous_method(request.method):
            if request.method == DELETE:
                struct.append({"id": view.kwargs["pk"]})
            [check_is_allowed_to_change_policy(p, r_u.id) for p in struct]
        return True
