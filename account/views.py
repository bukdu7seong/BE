import json
import random
import string
from datetime import timedelta, timezone, datetime

import pytz
import requests
from django.conf import settings
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.db import transaction, IntegrityError
from rest_framework import status, generics
from rest_framework.decorators import action, permission_classes, api_view
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, EmailVerification
from .serializer import UserSigninSerializer, UserSignupSerializer, UserDetailSerializer, UserImageUpdateSerializer
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
        if user.is_2fa:
            code = EmailService.send_verification_email(user.email)
            try:
                verification = user.emailverification
                verification.code = code
                verification.type = 'LOGIN'
                verification.save()
            except EmailVerification.DoesNotExist:
                verification = EmailVerification(user=user, code=code)
                verification.save()
            return Response(status=status.HTTP_301_MOVED_PERMANENTLY)
        return self._get_user_token(request)

    @transaction.atomic
    @action(detail=False, methods=['post'], url_path='2fa')
    def verify_email(self, request):
        code = request.data.get('code')
        email = request.data.get('email')
        user = User.objects.get(email=email)
        if user.emailverification.code == code:
            if datetime.now(pytz.UTC) - user.emailverification.updated_at > timedelta(seconds=5):
                raise exceptions.TwoFactorException("code is expired", status.HTTP_400_BAD_REQUEST)
            user.emailverification.delete()
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        else:
            raise ValidationError("Invalid code")

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
                    EmailService.send_verification_email(user.email)
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
    def get_verification_code(cls):
        random_value = string.ascii_letters + string.digits
        random_value = list(random_value)
        random.shuffle(random_value)
        code = "".join(random_value[:6])
        return code

    @classmethod
    def send_verification_email(cls, email):
        code = cls.get_verification_code()
        content = "다음 코드를 인증창에 입력해주세요.\n" + code
        to = [email]
        mail = EmailMessage("Verification code for TS", content, to=to)
        mail.send()
        return code


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
    

class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    lookup_field = 'username'
    permission_classes = [IsAuthenticated]  # 인증된 사용자만 접근 가능


from game.models import Game

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile_stats(request):
    user = request.user
    # player2가 존재하는 게임만 고려
    games_won = Game.objects.filter(winner=user, player2__isnull=False).count()
    games_lost = Game.objects.filter(loser=user, player2__isnull=False).count()
    total_games = games_won + games_lost
    win_rate = (games_won / total_games * 100) if total_games > 0 else 0

    user_info = {
        "user_id": user.id,
        "email": user.email,
        "username": user.username,
        "img": user.image.url if user.image else None,
    }

    game_info = {
        "win_rate": win_rate,
        "wins": games_won,
        "losses": games_lost,
    }

    return Response({
        "user_info": user_info,
        "game_info": game_info,
    })

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def change_username(request):
    user = request.user
    new_username = request.data.get('new_username')
    if not new_username:
        return Response({'error': '새로운 username을 제공해야 합니다.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user.username = new_username
        user.save()
        return Response({'message': 'username이 성공적으로 변경되었습니다.'}, status=status.HTTP_200_OK)
    except IntegrityError:
        return Response({'error': '이미 존재하는 username입니다.'}, status=status.HTTP_409_CONFLICT)
    
class UpdateUserImageView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        user = request.user
        serializer = UserImageUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)