from django.apps import AppConfig
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out


class LogincheckConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "loginCheck"