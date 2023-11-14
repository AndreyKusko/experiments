import pytest
from django.contrib.auth import get_user_model

from accounts.models.token import Token
from ma_saas.constants.system import Callable

User = get_user_model()


@pytest.fixture
def get_authorization_token_instance_fi() -> Callable:
    def get_token(user: User) -> str:
        instance, _ = Token.objects.get_or_create(user=user)
        return instance

    return get_token


@pytest.fixture
def get_authorization_token_fi(get_authorization_token_instance_fi: Callable) -> Callable:
    def get_token(user: User) -> str:
        token = get_authorization_token_instance_fi(user=user)
        return f"Token {token.key}"

    return get_token


@pytest.fixture
def super_u_token_fi(get_authorization_token_fi: Callable, super_user_fi: Callable) -> str:
    return get_authorization_token_fi(user=super_user_fi)


@pytest.fixture
def regular_u_token_fi(get_authorization_token_fi: Callable, regular_u_fi: User) -> str:
    return get_authorization_token_fi(user=regular_u_fi)
