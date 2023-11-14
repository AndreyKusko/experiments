async def retrieve_target_email(target_user, notification):
    contact = notification.target_email
    if target_user:
        contact = contact or target_user.get("email")
    return contact


async def retrieve_target_phone(target_user, notification):
    contact = notification.target_phone
    if target_user:
        contact = contact or target_user.get("phone")
    return contact


async def retrieve_target_push_token(target_user, notification):
    tokens = [notification.target_push_token] if notification.target_push_token else []
    if target_user:
        tokens = target_user.get("push_tokens", [])
    return tokens
