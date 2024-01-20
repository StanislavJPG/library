import smtplib
import uuid
from email.message import EmailMessage
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, UUIDIDMixin

from src.config import MAIL_NAME, MAIL_PASS
from src.database import User, get_user_db


SECRET = "SECRET"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        email = EmailMessage()
        email['Subject'] = 'Підтвердити пошту'
        email['From'] = MAIL_NAME
        email['To'] = user.email

        email.set_content(
            f"""
            <div style="text-align: center; margin: auto; width: 50%;">
                <p>
                    <b style="font-size: 20px;">Нікому не повідомляйте цей код!</b>
                </p>
                <b style="font-size: 30px;">Ваш код підтвердження: </b>
                <div style="border: 1px solid #ccc; margin: 10px; padding: 10px; text-align: center; border-radius: 10px; margin: auto;">
                    <a style="font-size: 15px; font-family: 'Lucida Console', 'Courier New', monospace;">{token}</a>
                </div>
                <p style="font-size: 15px;">Скопіюйте цей код підтвердження та вставте його у вікно на сайті.</p>
            </div>

                """"",
            subtype='html'
        )

        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(MAIL_NAME, MAIL_PASS)
            server.send_message(email)

    async def on_after_verify(
            self, user: User, request: Optional[Request] = None
    ):
        print(f"User {user.id} has been verified")


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)
