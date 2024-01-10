import uuid

from fastapi_users import FastAPIUsers
from fastapi_users.authentication import CookieTransport, AuthenticationBackend
from fastapi_users.authentication import JWTStrategy

from src.auth.manager import get_user_manager
from src.database import User

cookie_transport = CookieTransport(cookie_max_age=10800, cookie_name='U_CONF')

SECRET = "SECRET"


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
current_user = fastapi_users.authenticator.current_user(optional=True)

current_active_user = fastapi_users.current_user()
