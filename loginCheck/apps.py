from django.apps import AppConfig
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out


class LogincheckConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "loginCheck"

    def ready(self):
        # 사용자 로그인 및 로그아웃 신호에 대한 수신자(receiver) 등록
        user_logged_in.connect(user_logged_in_receiver)
        user_logged_out.connect(user_logged_out_receiver)
        print("1111111")


@receiver(user_logged_in)
def user_logged_in_receiver(sender, request, user, **kwargs):
    # 여기서 사용자의 로그인 상태를 업데이트하고, 필요한 WebSocket 메시지를 전송할 수 있음
    print("22222222")
    pass


@receiver(user_logged_out)
def user_logged_out_receiver(sender, request, user, **kwargs):
    print("3333333333")
    # 여기서 사용자의 로그아웃 상태를 업데이트하고, 필요한 WebSocket 메시지를 전송할 수 있음
    pass