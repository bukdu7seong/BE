import json
import random
import string
from typing import Literal
from datetime import timedelta, datetime

import pytz
import requests
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.mail import EmailMessage
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from rest_framework import generics, status
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from game.models import Game
from .models import EmailVerification, User
from .serializer import (User2FASerializer, UserDetailSerializer, UserImageUpdateSerializer, UserLanguageUpdateSerializer,
                         UserProfileStatsSerializer, UserSigninSerializer, UserSignupSerializer)
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
            data = { 'email': user.email }
            code = EmailService.send_verification_email(user, 'login')
            return Response(data, status=status.HTTP_301_MOVED_PERMANENTLY)
        return self._get_user_token(request)

    @action(detail=False, methods=['get'], url_path='check')
    def checkUsername(self, request):
        username = request.query_params.get('username')
        if not username:
            return Response({"error": "username parameter is missing."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(False, status=status.HTTP_200_OK)
        return Response(True, status=status.HTTP_200_OK)


    @transaction.atomic
    @action(detail=False, methods=['post'], url_path='2fa')
    def verify_login_2fa(self, request):
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

    @action(methods=['post'], detail=False, url_path='2fa/re')
    @transaction.atomic
    def resend_verification_email(self, request):
        email = request.data.get('email')
        user = User.objects.get(email=email)
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
                    data = { 'email': user.email }
                    return Response(data, status=status.HTTP_301_MOVED_PERMANENTLY)
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
            raise exceptions.FTOauthException('토큰 발급에 실패 하였습니다.', status=status.HTTP_400_BAD_REQUEST)
        email = self._get_42_email(response)
        data = request.data.copy()
        data['email'] = email
        serializer = UserSignupSerializer(data=data)
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
                    user.is_verified = True
                    user.save()
                    return True
        return False

    @classmethod
    @transaction.atomic
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
    """
    특정 사용자의 상세 정보를 조회하는 API 엔드포인트입니다.
    - queryset: User 모델의 모든 인스턴스 대상.
    - serializer_class: UserDetailSerializer 사용.
    - lookup_field: 'username'을 통해 사용자 식별.
    - permission_classes: [IsAuthenticated]로 로그인한 사용자만 접근 가능.

    URL: 'api/account/search/<str:username>/'
    """

    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    lookup_field = 'username'
    permission_classes = [IsAuthenticated]

class UserProfileStatsView(APIView):
    """
    사용자 프로필 통계 정보 제공 API.
    - 로그인한 사용자만 접근 가능([IsAuthenticated]).
    - GET: 사용자의 게임 승률, 승리/패배 횟수 등 통계 정보 제공.
    - URL: 'api/account/user/profile-stats/'

    게임 승률은 승리한 게임 수를 총 게임 수로 나눈 후 100을 곱해 계산.
    응답에는 사용자 기본 정보와 게임 통계 정보 포함.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        # player2가 존재하는 게임만 고려
        games_won = Game.objects.filter(winner=user, player2__isnull=False).count()
        games_lost = Game.objects.filter(loser=user, player2__isnull=False).count()
        total_games = games_won + games_lost
        win_rate = (games_won / total_games * 100) if total_games > 0 else 0

        user_info = {
            "user_id": user.id,
            "username": user.username,
            "img": user.image.url,
            "language": user.language,
            "is_2fa": user.is_2fa,
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

class ChangeUsernameView(APIView):
    """
    사용자의 username 변경 API.
    - 접근: 로그인한 사용자([IsAuthenticated]).
    - PATCH: 'new_username'으로 username 변경.
    - URL: 'change-username/'

    성공 시 변경된 username 정보 반환, 실패 시 에러 메시지 반환.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def patch(self, request, *args, **kwargs):
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
    """
    사용자 프로필 이미지 업데이트 API.
    - 접근: 로그인한 사용자([IsAuthenticated]).
    - PATCH: 이미지 파일로 프로필 이미지 업데이트.
    - URL: 'update-image/'

    성공 시 업데이트된 이미지 정보 반환, 실패 시 에러 메시지 반환.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        user = request.user
        serializer = UserImageUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(generics.UpdateAPIView):
    """
    사용자 비밀번호 변경 API.
    - 접근: 로그인한 사용자([IsAuthenticated]).
    - PATCH: 'old_password'와 'new_password' 사용하여 비밀번호 변경.
    - URL: 'change-password/'

    기존 비밀번호 일치 시 새 비밀번호로 업데이트, 일치하지 않으면 에러 메시지 반환.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserDetailSerializer

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        if not user.check_password(old_password):
            return Response({"error": "기존 비밀번호가 일치하지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)
        user.password = make_password(new_password)
        user.save()
        return Response({"message": "비밀번호가 성공적으로 변경되었습니다."}, status=status.HTTP_200_OK)


class OtherUserProfileStatsView(APIView):
    """
    다른 사용자의 프로필 통계 정보 조회 API.
    - 접근: 로그인한 사용자([IsAuthenticated]).
    - GET: 'user_id'를 통해 특정 사용자의 게임 승률, 승리/패배 횟수 등 조회.
    - URL: 'api/account/user-stats/<int:user_id>/'

    사용자를 찾을 수 없는 경우 404 응답 반환.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            serializer = UserProfileStatsSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({'error': '사용자를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)


class UpdateUser2FAView(APIView):
    """
    사용자의 2단계 인증(2FA) 설정 업데이트 API.
    - 접근: 로그인한 사용자([IsAuthenticated]).
    - PATCH: 'is_2fa'로 2FA 설정 업데이트.
    - URL: 'update-2fa/'

    성공 시 업데이트된 2FA 설정 정보 반환, 실패 시 에러 메시지 반환.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        user = request.user
        if not set(request.data.keys()).issubset({'is_2fa'}):
            return Response({"error": "유효하지 않은 요청입니다."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = User2FASerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "2FA 설정이 업데이트 되었습니다."})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class UpdateUserLanguageView(APIView):
    """
    사용자 선호 언어 설정 업데이트 API.
    - 접근: 로그인한 사용자([IsAuthenticated]).
    - PATCH: 'language'로 언어 설정 업데이트.
    - URL: 'update-language/'

    성공 시 업데이트된 언어 설정 정보 반환, 실패 시 에러 메시지 반환.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        user = request.user
        if not set(request.data.keys()).issubset({'language'}):
            return Response({"error": "유효하지 않은 요청입니다."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserLanguageUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "언어 설정이 업데이트 되었습니다."})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserDeleteView(APIView):
    """
    사용자 계정 삭제 API.
    - 접근: 로그인한 사용자([IsAuthenticated]).
    - DELETE: 사용자 계정 삭제.
    - URL: 'delete-account/'

    성공 시 성공 메시지 반환, 실패 시 에러 메시지 반환.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        password = request.data.get('password')
        user = request.user
        if user.check_password(password):
            user.delete()
            return Response({"message": "회원 탈퇴가 성공적으로 처리되었습니다."}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"message": "비밀번호가 올바르지 않습니다."}, status=status.HTTP_403_FORBIDDEN)

class Request2FAView(APIView):
    """
    2FA 코드 이메일 전송 API.
    - 접근: 로그인한 사용자([IsAuthenticated]).
    - POST: 사용자 이메일로 2FA 코드 전송.
    - URL: 'request-2fa/'

    이메일 주소 제공 시 2FA 코드 전송, 없거나 사용자 미존재 시 에러 반환.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "이메일 주소가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        if request.user.is_authenticated and request.user.email == email:
            return Response({"error": "자신의 이메일로는 2FA 코드를 요청할 수 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "해당 이메일의 사용자를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        
        # 실제로 이메일 전송
        EmailService.send_verification_email(user, '2fa')
        
        return Response({"message": "2FA 코드가 이메일로 발송되었습니다."}, status=status.HTTP_200_OK)

class Verify2FAView(APIView):
    """
    2FA 코드 검증 API.
    - 접근: 로그인한 사용자([IsAuthenticated]).
    - POST: 이메일, 2FA 코드, 게임 ID를 사용하여 2FA 코드 검증 및 게임 정보 업데이트.
    - URL: 'verify-2fa/'

    이메일, 2FA 코드, 게임 ID 제공 시 코드 검증 및 게임 정보 업데이트, 실패 시 에러 메시지 반환.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')
        game_id = request.data.get('game_id')  # 게임 ID 추가

        if not email or not code or not game_id:
            return Response({"error": "이메일 주소, 2FA 코드, 게임 ID가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "해당 이메일의 사용자를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        
        if EmailService.verify_email(user, code, '2fa'):
            try:
                game = Game.objects.get(game_id=game_id)
                if game.player2 is not None:
                    return Response({"error": "이미 player2가 등록된 게임입니다."}, status=status.HTTP_400_BAD_REQUEST)
                
                # 2FA 인증이 성공하면, player2를 업데이트
                game.player2 = user
                # winner와 loser 중 null인 필드에 player2를 할당
                if game.winner is None and game.loser is not None:
                    game.winner = user
                elif game.loser is None and game.winner is not None:
                    game.loser = user
                game.save()
                return Response({"message": "2FA 인증이 성공적으로 완료되었으며, 게임 결과가 업데이트 되었습니다."}, status=status.HTTP_200_OK)
            except Game.DoesNotExist:
                return Response({"error": "해당 게임 ID의 게임을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"error": "2FA 코드가 일치하지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)
