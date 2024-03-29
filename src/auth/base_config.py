import uuid

from fastapi_users import FastAPIUsers
from fastapi_users.authentication import CookieTransport, AuthenticationBackend
from fastapi_users.authentication import JWTStrategy

from src.auth.manager import get_user_manager
from src.database import User
from src.config import SECRET

cookie_transport = CookieTransport(cookie_max_age=None, cookie_name='U_CONF')


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=10800)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

current_superuser = fastapi_users.current_user(active=True, superuser=True)
current_user = fastapi_users.current_user()

current_optional_user = fastapi_users.authenticator.current_user(optional=True)
current_optional_superuser = fastapi_users.current_user(active=True, superuser=True, optional=True)
