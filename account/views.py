import json
import requests
import string, random

from django.http import HttpResponse
from django.conf import settings
from django.core.mail import EmailMessage

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action, permission_classes
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializer import UserSigninSerializer


# redirect to 42oauth page
@permission_classes([AllowAny])
class FtAuthView(APIView):
    def get(self, request):
        redirect_uri = (f"{settings.FT_AUTH_CONFIG['authorization_uri']}"
                        f"?client_id={settings.FT_OAUTH_CONFIG['client_id']}"
                        f"&redirect_uri={settings.FT_OAUTH_CONFIG['redirect_uri']}"
                        f"&response-type=code")
        return HttpResponse(json.dumps({'url': redirect_uri}), status=status.HTTP_200_OK)


# Login View
@permission_classes([AllowAny])
class MyLoginView(ViewSet):
    @action(detail=False, methods=['post'], url_path='login')
    def login_account(self, request):
        username = request.data.get('username')
        try:
            user = User.objects.get(username=username)
            if user.is_2fa:
                EmailService.send_verification_email(user.email)
                return Response(status=status.HTTP_301_MOVED_PERMANENTLY)
            return self._get_user_token(request)
        except User.DoesNotExist:
            return Response('have to redirect to sign up', status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'], url_path='42code')
    def ft_login(self, request):
        code = request.query_params.get('code', None)
        if code is not None:
            response = self._get_42_access_token(code)
            if response.status_code == 200:
                email = self._get_42_email(response)
                try:
                    user = User.objects.get(email=email)
                    if user.is_2fa:
                        EmailService.send_verification_email(user.email)
                        return Response(status=status.HTTP_301_MOVED_PERMANENTLY)
                    request.data['email'] = email
                    refresh = RefreshToken.for_user(user)
                    return Response({
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    })

                except User.DoesNotExist:
                    return Response(email, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response('fail to get 42 access token', status=400)
        else:
            return Response('fail to get code', status=400)

    @classmethod
    def _get_42_email(cls, response):
        js = response.json()
        token = js.get('access_token')
        user_info = requests.get(settings.FT_AUTH_CONFIG['user_info_uri'], headers={'Authorization': 'Bearer ' + token})
        if user_info.status_code == 200:
            return user_info.json()['email']
        else:
            return None

    @classmethod
    def _get_42_access_token(cls, code):
        data = {
            "grant_type": "authorization_code",
            "client_id": settings.FT_AUTH_CONFIG['client_id'],
            "client_secret": settings.FT_AUTH_CONFIG['client_secret'],
            "code": code,
            "redirect_uri": settings.FT_AUTH_CONFIG['auth_redirect_uri'],
        }
        try:
            return requests.post(settings.FT_AUTH_CONFIG['token_uri'], data=data)
        except requests.exceptions.RequestException as e:
            return HttpResponse(str(e), status=500)

    @classmethod
    def _get_user_token(cls, request):
        serializer = UserSigninSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailService:
    @classmethod
    def get_verification_code(cls):
        random_value = string.ascii_letters + string.digits
        random_value = list(random_value)
        random.shuffle(random_value)
        code = "".join(random_value[:6])
        return code

    @classmethod
    def send_verification_email(cls, email):
        content = "다음 코드를 인증창에 입력해주세요.\n" + cls.get_verification_code()
        title = "Verification Code"
        to = [email]
        mail = EmailMessage("Verification code for TS", content, to=["kikiwjh@gmail.com"])
        mail.send()
        print("send here")


# SignUp View
@permission_classes(AllowAny)
class SignupView(APIView):
    def post(self, request):
        data = json.loads(request.body)
        try:
            user = User.objects.create_user(
                username=data.get('username'),
                email=data.get('email'),
                password=data.get('password'),
            )
        except ValidationError as e:
            return Response({"message": e.messages[0]}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            return Response({"message": "integrity Error"}, status=status.HTTP_400_BAD_REQUEST)
        user.save()
        return Response({"message": "ok"}, status=status.HTTP_201_CREATED)


@permission_classes([IsAuthenticated])
class TestView(APIView):
    def get(self, request, *args, **kwargs):
        return HttpResponse("ok")
