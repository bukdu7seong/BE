import json
import random
import string

from typing import Literal
from datetime import timedelta, timezone, datetime

import pytz
import requests
from django.conf import settings
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, EmailVerification
from .serializer import UserSigninSerializer, UserSignupSerializer
from ts import exceptions


# redirect to 42oauth page
@permission_classes([AllowAny])
class FtAuthView(APIView):
    def get(self, request):
        redirect_uri = (f"{settings.FT_OAUTH_CONFIG['authorization_uri']}"
                        f"?client_id={settings.FT_OAUTH_CONFIG['client_id']}"
                        f"&redirect_uri={settings.FT_OAUTH_CONFIG['redirect_uri']}"
                        f"&response_type=code")
        return HttpResponse(json.dumps({'url': redirect_uri}), status=status.HTTP_200_OK)


# Login View
@permission_classes([AllowAny])
class MyLoginView(ViewSet):
    @action(methods=['post'], detail=False, url_path='devlogin')
    def login_dev(self, request):
        return self._get_user_token(request)

    @transaction.atomic
    @action(detail=False, methods=['post'], url_path='signin')
    def login_account(self, request):
        username = request.data.get('username')
        user = User.objects.get(username=username)
        serializer = UserSigninSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if user.is_2fa or not user.is_verified:
            code = EmailService.send_verification_email(user, 'login')
            return Response(status=status.HTTP_301_MOVED_PERMANENTLY)
        return self._get_user_token(request)

    @transaction.atomic
    @action(detail=False, methods=['post'], url_path='2fa')
    def verify_email(self, request):
        code = request.data.get('code')
        email = request.data.get('email')
        user = User.objects.get(email=email)
        if EmailService.verify_email(user, code, 'login'):
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        else:
            raise ValidationError("Invalid code")

    @action(methods=['get'], detail=False, url_path='2fa')
    @transaction.atomic
    def resend_verification_email(self, request):
        email = request.data.get('email')
        user = User.objects.get(email=request.data.get(email))
        verification = user.emailverification
        EmailService.send_verification_email(user, verification.type)
        return Response(status.HTTP_200_OK)

    @transaction.atomic
    @action(detail=False, methods=['post'], url_path='42code')
    def ft_login(self, request):
        code = request.query_params.get('code', None)
        if code is not None:
            response = self._get_42_access_token(code)
            print(response.content)
            if response.status_code == 200:
                email = self._get_42_email(response)
                user = User.objects.get(email=email)
                if user.is_2fa:
                    EmailService.send_verification_email(user, 'login')
                    return Response(status=status.HTTP_301_MOVED_PERMANENTLY)
                request.data['email'] = email
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                })
            else:
                raise exceptions.FTOauthException('fail to get 42 access token', status=status.HTTP_400_BAD_REQUEST)
        else:
            raise ValueError('fail to get code')

    @transaction.atomic
    @action(detail=False, methods=['post'], url_path='signup')
    def signup(self, request):
        code = request.data.get('code')
        response = self._get_42_access_token(code)
        if response.status_code != 200:
            raise exceptions.FTOauthException('토큰 발급에 실패 하였습니다.')
        email = self._get_42_email(response)
        request.data['email'] = email
        serializer = UserSignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            user = User.objects.get(email=email)
            EmailService.send_verification_email(user, 'login')
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            raise ValidationError('invalid input')

    @classmethod
    def _get_42_email(cls, response):
        js = response.json()
        token = js.get('access_token')
        user_info = requests.get(settings.FT_OAUTH_CONFIG['user_info_uri'],
                                 headers={'Authorization': 'Bearer ' + token})
        if user_info.status_code == 200:
            return user_info.json()['email']
        else:
            return None

    @classmethod
    def _get_42_access_token(cls, code):
        data = {
            "grant_type": "authorization_code",
            "client_id": settings.FT_OAUTH_CONFIG['client_id'],
            "client_secret": settings.FT_OAUTH_CONFIG['client_secret'],
            "code": code,
            "redirect_uri": settings.FT_OAUTH_CONFIG['redirect_uri'],
        }
        return requests.post(settings.FT_OAUTH_CONFIG['token_uri'], data=data)

    @classmethod
    def _get_user_token(cls, request):
        serializer = UserSigninSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        else:
            raise ValidationError("Invalid request")


class EmailService:
    @classmethod
    @transaction.atomic
    def verify_email(cls, user, code, code_type):
        verification = user.emailverification
        if verification.type == code_type:
            if verification.code == code:
                if datetime.now(pytz.UTC) - user.emailverification.updated_at < timedelta(minutes=5):
                    verification.delete()
                    return True
        return False

    @classmethod
    def email_verification_update(cls, user, code, code_type: Literal['login', 'pass', 'game'] = 'game'):
        try:
            verification = user.emailverification
            verification.code = code
            verification.type = code_type
            verification.save()
        except EmailVerification.DoesNotExist:
            verification = EmailVerification(user=user, code=code, type=code_type)
            verification.save()

    @classmethod
    def get_verification_code(cls):
        random_value = string.ascii_letters + string.digits
        random_value = list(random_value)
        random.shuffle(random_value)
        code = "".join(random_value[:6])
        return code

    @classmethod
    @transaction.atomic
    def send_verification_email(cls, user, code_type: Literal['login', 'pass', 'game']):
        code = cls.get_verification_code()
        cls.email_verification_update(user, code, code_type)
        content = "다음 코드를 인증창에 입력해주세요.\n" + code
        to = [user.email]
        mail = EmailMessage("Verification code for TS", content, to=to)
        mail.send()

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]


# SignUp View
@permission_classes([AllowAny])
class SignupView(APIView):
    @transaction.atomic
    def post(self, request):
        serializer = UserSignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            raise ValidationError('invalid input')


@permission_classes([IsAuthenticated])
class TestView(APIView):
    def get(self, request, *args, **kwargs):
        return HttpResponse("ok")


from rest_framework import generics
from .serializer import UserDetailSerializer
from rest_framework.permissions import IsAuthenticated


class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    lookup_field = 'username'
    permission_classes = [IsAuthenticated]  # 인증된 사용자만 접근 가능
