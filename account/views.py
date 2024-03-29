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
        try:
            user = User.objects.get(request.data.get('username'))
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

    @action(methods=['get'], detail=False, url_path='2fa/re')
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
    UserDetailView는 Django REST Framework의 generics.RetrieveAPIView를 상속받아 구현된 클래스 뷰입니다.
    이 뷰는 특정 사용자의 상세 정보를 조회하는 API 엔드포인트를 제공합니다.

    - queryset: User 모델의 모든 인스턴스를 대상으로 합니다. 이를 통해 데이터베이스에서 사용자 정보를 조회할 수 있습니다.
    - serializer_class: UserDetailSerializer를 사용하여 조회된 사용자 정보를 직렬화합니다. 이를 통해 클라이언트에게 전달될 데이터의 형식을 정의합니다.
    - lookup_field: URL에서 사용자를 식별하기 위한 필드로 'username'을 사용합니다. 이는 URL 경로에 포함된 username 값을 통해 특정 사용자를 조회할 수 있게 합니다.
    - permission_classes: [IsAuthenticated]를 통해 이 뷰에 접근할 수 있는 사용자를 인증된 사용자로 제한합니다. 즉, 로그인한 사용자만이 이 API를 통해 사용자 정보를 조회할 수 있습니다.

    이 클래스 뷰는 'api/account/search/<str:username>/' URL 패턴에 연결되어 있으며, 해당 URL로 GET 요청이 들어오면 지정된 username에 해당하는 사용자의 상세 정보를 반환합니다.
    """

    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    lookup_field = 'username'
    permission_classes = [IsAuthenticated]

class UserProfileStatsView(APIView):
    """
    UserProfileStatsView는 사용자의 프로필 통계 정보를 제공하는 API 엔드포인트입니다.
    이 뷰는 Django REST Framework의 APIView를 상속받아 구현되었습니다.

    - permission_classes: [IsAuthenticated]를 사용하여 이 API 엔드포인트에 접근할 수 있는 사용자를 인증된 사용자로 제한합니다. 즉, 로그인한 사용자만이 자신의 프로필 통계 정보를 조회할 수 있습니다.

    GET 요청:
    이 뷰는 GET 요청을 처리하여 사용자의 게임 승률, 승리 횟수, 패배 횟수 등의 통계 정보를 제공합니다. 
    - 사용자는 request.user를 통해 인증된 사용자 객체를 얻습니다.
    - player2가 존재하는 게임만을 대상으로 하여, 사용자가 승리한 게임의 수(games_won)와 패배한 게임의 수(games_lost)를 계산합니다.
    - 총 게임 수(total_games)는 승리한 게임의 수와 패배한 게임의 수의 합입니다.
    - 승률(win_rate)은 승리한 게임의 수를 총 게임 수로 나눈 후 100을 곱하여 계산합니다. 총 게임 수가 0인 경우 승률은 0으로 처리합니다.
    - 사용자의 기본 정보(user_info)와 게임 통계 정보(game_info)를 포함한 응답을 반환합니다.

    이 클래스 뷰는 'api/account/user/profile-stats/' URL 패턴에 연결되어 있으며, 해당 URL로 GET 요청이 들어오면 인증된 사용자의 프로필 통계 정보를 반환합니다.
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
    ChangeUsernameView는 사용자의 username을 변경하는 API 엔드포인트를 제공합니다.
    이 뷰는 Django REST Framework의 APIView를 상속받아 구현되었습니다.

    - permission_classes: [IsAuthenticated]를 사용하여 이 API 엔드포인트에 접근할 수 있는 사용자를 인증된 사용자로 제한합니다. 즉, 로그인한 사용자만이 자신의 username을 변경할 수 있습니다.

    PATCH 요청:
    이 뷰는 PATCH 요청을 처리하여 사용자의 username을 변경합니다.
    - 사용자는 request.user를 통해 인증된 사용자 객체를 얻습니다.
    - request.data에서 'new_username' 키를 통해 전달받은 새로운 username 값을 사용자 객체에 저장합니다.
    - username이 성공적으로 변경되면, 변경된 username 정보를 포함한 응답을 반환합니다.
    - 만약 새로운 username이 이미 다른 사용자에 의해 사용 중인 경우, IntegrityError 예외가 발생하며, 이에 대한 에러 메시지를 응답으로 반환합니다.

    이 클래스 뷰는 'change-username/' URL 패턴에 연결되어 있으며, 해당 URL로 PATCH 요청이 들어오면 인증된 사용자의 username을 변경하는 처리를 수행합니다.

    주요 처리 과정:
    1. 인증된 사용자 객체를 request.user를 통해 얻습니다.
    2. request.data에서 'new_username' 값을 추출합니다.
    3. 추출한 'new_username' 값으로 사용자의 username을 업데이트합니다.
    4. username 변경이 성공적으로 이루어지면, 변경된 정보를 포함한 응답을 클라이언트에게 반환합니다.
    5. 변경하려는 username이 이미 존재하는 경우, IntegrityError 예외를 처리하고, 적절한 에러 메시지를 응답으로 반환합니다.
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
    UpdateUserImageView는 사용자의 프로필 이미지를 업데이트하는 API 엔드포인트를 제공합니다.
    이 뷰는 Django REST Framework의 APIView를 상속받아 구현되었습니다.

    - permission_classes: [IsAuthenticated]를 사용하여 이 API 엔드포인트에 접근할 수 있는 사용자를 인증된 사용자로 제한합니다. 즉, 로그인한 사용자만이 자신의 프로필 이미지를 업데이트할 수 있습니다.

    PATCH 요청:
    이 뷰는 PATCH 요청을 처리하여 사용자의 프로필 이미지를 업데이트합니다.
    - 사용자는 request.user를 통해 인증된 사용자 객체를 얻습니다.
    - request.data에서 전달받은 이미지 파일을 사용자 객체의 이미지 필드에 저장합니다.
    - 이미지 업데이트가 성공적으로 이루어지면, 업데이트된 이미지 정보를 포함한 응답을 반환합니다.
    - 이미지 업데이트 과정에서 오류가 발생한 경우, 해당 에러 메시지를 응답으로 반환합니다.

    이 클래스 뷰는 'update-image/' URL 패턴에 연결되어 있으며, 해당 URL로 PATCH 요청이 들어오면 인증된 사용자의 프로필 이미지를 업데이트하는 처리를 수행합니다.

    주요 처리 과정:
    1. 인증된 사용자 객체를 request.user를 통해 얻습니다.
    2. request.data를 사용하여 UserImageUpdateSerializer를 통해 이미지 데이터를 검증합니다.
    3. 검증이 성공하면, 사용자 객체의 이미지 필드를 업데이트하고 데이터베이스에 저장합니다.
    4. 이미지 업데이트가 성공적으로 이루어지면, 업데이트된 이미지 정보를 포함한 응답을 클라이언트에게 반환합니다.
    5. 이미지 업데이트 과정에서 오류가 발생한 경우, 적절한 에러 메시지를 응답으로 반환합니다.
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
    ChangePasswordView는 사용자의 비밀번호를 변경하는 API 엔드포인트를 제공합니다.
    이 뷰는 Django REST Framework의 generics.UpdateAPIView를 상속받아 구현되었습니다.

    - permission_classes: [IsAuthenticated]를 사용하여 이 API 엔드포인트에 접근할 수 있는 사용자를 인증된 사용자로 제한합니다. 즉, 로그인한 사용자만이 자신의 비밀번호를 변경할 수 있습니다.

    PATCH 요청:
    이 뷰는 PATCH 요청을 처리하여 사용자의 비밀번호를 변경합니다.
    - 사용자는 request.user를 통해 인증된 사용자 객체를 얻습니다.
    - request.data에서 'old_password'와 'new_password' 키를 통해 전달받은 기존 비밀번호와 새로운 비밀번호 값을 사용합니다.
    - 기존 비밀번호가 일치하는 경우에만 새로운 비밀번호로 업데이트합니다.
    - 비밀번호 변경이 성공적으로 이루어지면, 성공 메시지를 포함한 응답을 반환합니다.
    - 기존 비밀번호가 일치하지 않는 경우, 적절한 에러 메시지를 응답으로 반환합니다.

    이 클래스 뷰는 'change-password/' URL 패턴에 연결되어 있으며, 해당 URL로 PATCH 요청이 들어오면 인증된 사용자의 비밀번호를 변경하는 처리를 수행합니다.

    주요 처리 과정:
    1. 인증된 사용자 객체를 request.user를 통해 얻습니다.
    2. request.data에서 'old_password'와 'new_password' 값을 추출합니다.
    3. 사용자의 기존 비밀번호가 입력된 'old_password'와 일치하는지 확인합니다.
    4. 일치하는 경우, 'new_password' 값을 사용하여 사용자의 비밀번호를 업데이트합니다.
    5. 비밀번호 변경이 성공적으로 이루어지면, 성공 메시지를 포함한 응답을 클라이언트에게 반환합니다.
    6. 기존 비밀번호가 일치하지 않는 경우, 적절한 에러 메시지를 응답으로 반환합니다.
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
    OtherUserProfileStatsView는 다른 사용자의 프로필 통계 정보를 조회하는 API 엔드포인트를 제공합니다.
    이 뷰는 Django REST Framework의 APIView를 상속받아 구현되었습니다.

    - permission_classes: [IsAuthenticated]를 사용하여 이 API 엔드포인트에 접근할 수 있는 사용자를 인증된 사용자로 제한합니다. 즉, 로그인한 사용자만이 다른 사용자의 프로필 통계 정보를 조회할 수 있습니다.

    GET 요청:
    이 뷰는 GET 요청을 처리하여 특정 사용자의 게임 승률, 승리 횟수, 패배 횟수 등의 통계 정보를 제공합니다.
    - URL 경로에서 'user_id'를 통해 조회하고자 하는 사용자의 ID를 받습니다.
    - 해당 ID를 사용하여 데이터베이스에서 사용자 객체를 조회합니다.
    - 조회된 사용자 객체를 기반으로 UserProfileStatsSerializer를 사용하여 프로필 통계 정보를 직렬화하고, 이를 응답으로 반환합니다.
    - 만약 주어진 'user_id'에 해당하는 사용자를 찾을 수 없는 경우, 적절한 에러 메시지와 함께 404 Not Found 응답을 반환합니다.

    이 클래스 뷰는 'api/account/user-stats/<int:user_id>/' URL 패턴에 연결되어 있으며, 해당 URL로 GET 요청이 들어오면 지정된 사용자 ID에 해당하는 사용자의 프로필 통계 정보를 반환합니다.
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
    UpdateUser2FAView는 사용자의 2단계 인증(2FA) 설정을 업데이트하는 API 엔드포인트를 제공합니다.
    이 뷰는 Django REST Framework의 APIView를 상속받아 구현되었습니다.

    - permission_classes: [IsAuthenticated]를 사용하여 이 API 엔드포인트에 접근할 수 있는 사용자를 인증된 사용자로 제한합니다. 즉, 로그인한 사용자만이 자신의 2FA 설정을 업데이트할 수 있습니다.

    PATCH 요청:
    이 뷰는 PATCH 요청을 처리하여 사용자의 2FA 설정을 업데이트합니다.
    - 사용자는 request.user를 통해 인증된 사용자 객체를 얻습니다.
    - request.data에서 'is_2fa' 키를 통해 전달받은 2FA 설정 값을 사용자 객체에 저장합니다.
    - 2FA 설정 업데이트가 성공적으로 이루어지면, 업데이트된 2FA 설정 정보를 포함한 응답을 반환합니다.
    - 2FA 설정 업데이트 과정에서 오류가 발생한 경우, 해당 에러 메시지를 응답으로 반환합니다.

    이 클래스 뷰는 'update-2fa/' URL 패턴에 연결되어 있으며, 해당 URL로 PATCH 요청이 들어오면 인증된 사용자의 2FA 설정을 업데이트하는 처리를 수행합니다.

    주요 처리 과정:
    1. 인증된 사용자 객체를 request.user를 통해 얻습니다.
    2. request.data를 사용하여 User2FASerializer를 통해 2FA 설정 데이터를 검증합니다.
    3. 검증이 성공하면, 사용자 객체의 2FA 설정을 업데이트하고 데이터베이스에 저장합니다.
    4. 2FA 설정 업데이트가 성공적으로 이루어지면, 업데이트된 2FA 설정 정보를 포함한 응답을 클라이언트에게 반환합니다.
    5. 2FA 설정 업데이트 과정에서 오류가 발생한 경우, 적절한 에러 메시지를 응답으로 반환합니다.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        user = request.user
        serializer = User2FASerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "2FA 설정이 업데이트 되었습니다."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UpdateUserLanguageView(APIView):
    """
    UpdateUserLanguageView는 사용자의 선호하는 언어 설정을 업데이트하는 API 엔드포인트를 제공합니다.
    이 뷰는 Django REST Framework의 APIView를 상속받아 구현되었습니다.

    - permission_classes: [IsAuthenticated]를 사용하여 이 API 엔드포인트에 접근할 수 있는 사용자를 인증된 사용자로 제한합니다. 즉, 로그인한 사용자만이 자신의 언어 설정을 업데이트할 수 있습니다.

    PATCH 요청:
    이 뷰는 PATCH 요청을 처리하여 사용자의 언어 설정을 업데이트합니다.
    - 사용자는 request.user를 통해 인증된 사용자 객체를 얻습니다.
    - request.data에서 'language' 키를 통해 전달받은 새로운 언어 설정 값을 사용자 객체에 저장합니다.
    - 언어 설정 업데이트가 성공적으로 이루어지면, 업데이트된 언어 설정 정보를 포함한 응답을 반환합니다.
    - 언어 설정 업데이트 과정에서 오류가 발생한 경우, 해당 에러 메시지를 응답으로 반환합니다.

    이 클래스 뷰는 'update-language/' URL 패턴에 연결되어 있으며, 해당 URL로 PATCH 요청이 들어오면 인증된 사용자의 언어 설정을 업데이트하는 처리를 수행합니다.

    주요 처리 과정:
    1. 인증된 사용자 객체를 request.user를 통해 얻습니다.
    2. request.data를 사용하여 UserLanguageUpdateSerializer를 통해 언어 설정 데이터를 검증합니다.
    3. 검증이 성공하면, 사용자 객체의 언어 설정을 업데이트하고 데이터베이스에 저장합니다.
    4. 언어 설정 업데이트가 성공적으로 이루어지면, 업데이트된 언어 설정 정보를 포함한 응답을 클라이언트에게 반환합니다.
    5. 언어 설정 업데이트 과정에서 오류가 발생한 경우, 적절한 에러 메시지를 응답으로 반환합니다.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        user = request.user
        serializer = UserLanguageUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "언어 설정이 업데이트 되었습니다."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserDeleteView(APIView):
    """
    UserDeleteView는 사용자 계정을 삭제하는 API 엔드포인트를 제공합니다.
    이 뷰는 Django REST Framework의 APIView를 상속받아 구현되었습니다.

    - permission_classes: [IsAuthenticated]를 사용하여 이 API 엔드포인트에 접근할 수 있는 사용자를 인증된 사용자로 제한합니다. 즉, 로그인한 사용자만이 자신의 계정을 삭제할 수 있습니다.

    DELETE 요청:
    이 뷰는 DELETE 요청을 처리하여 사용자의 계정을 삭제합니다.
    - 사용자는 request.user를 통해 인증된 사용자 객체를 얻습니다.
    - 사용자 객체를 삭제하고, 성공적으로 처리되면, 성공 메시지를 포함한 응답을 반환합니다.
    - 계정 삭제 과정에서 오류가 발생한 경우, 해당 에러 메시지를 응답으로 반환합니다.

    이 클래스 뷰는 'delete-account/' URL 패턴에 연결되어 있으며, 해당 URL로 DELETE 요청이 들어오면 인증된 사용자의 계정을 삭제하는 처리를 수행합니다.

    주요 처리 과정:
    1. 인증된 사용자 객체를 request.user를 통해 얻습니다.
    2. 사용자 객체를 데이터베이스에서 삭제합니다.
    3. 계정 삭제가 성공적으로 이루어지면, 성공 메시지를 포함한 응답을 클라이언트에게 반환합니다.
    4. 계정 삭제 과정에서 오류가 발생한 경우, 적절한 에러 메시지를 응답으로 반환합니다.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        user = request.user
        user.delete()
        return Response({"message": "회원 탈퇴가 성공적으로 처리되었습니다."}, status=status.HTTP_204_NO_CONTENT)
    
class Request2FAView(APIView):
    """
    Request2FAView는 사용자에게 2단계 인증(2FA) 코드를 이메일로 전송하는 API 엔드포인트를 제공합니다.
    이 뷰는 Django REST Framework의 APIView를 상속받아 구현되었습니다.

    - permission_classes: [IsAuthenticated]를 통해 이 뷰에 접근할 수 있는 사용자를 인증된 사용자로 제한합니다. 즉, 로그인한 사용자만이 이 API를 통해 사용자 정보를 조회할 수 있습니다.

    POST 요청:
    이 뷰는 POST 요청을 처리하여 사용자의 이메일 주소로 2FA 코드를 전송합니다.
    - 요청에서 'email' 키를 통해 전달받은 이메일 주소를 사용하여 해당 이메일 주소를 가진 사용자를 데이터베이스에서 조회합니다.
    - 해당 사용자가 존재하지 않는 경우, 적절한 에러 메시지와 함께 404 Not Found 응답을 반환합니다.
    - 사용자가 존재하는 경우, EmailService 클래스를 사용하여 2FA 코드를 생성하고, 이메일 인증 정보를 업데이트한 후, 
      생성된 2FA 코드를 사용자의 이메일 주소로 전송합니다.
    - 2FA 코드 전송이 성공적으로 완료되면, 성공 메시지를 포함한 응답을 반환합니다.

    이 클래스 뷰는 'request-2fa/' URL 패턴에 연결되어 있으며, 해당 URL로 POST 요청이 들어오면 사용자의 이메일 주소로 2FA 코드를 전송하는 처리를 수행합니다.

    주요 처리 과정:
    1. POST 요청에서 'email' 키를 통해 전달받은 이메일 주소를 사용하여 데이터베이스에서 해당 이메일 주소를 가진 사용자를 조회합니다.
    2. 해당 사용자가 존재하지 않는 경우, 적절한 에러 메시지와 함께 404 Not Found 응답을 반환합니다.
    3. 사용자가 존재하는 경우, EmailService 클래스의 get_verification_code 메서드를 호출하여 2FA 코드를 생성합니다.
    4. 생성된 2FA 코드와 '2fa' 타입을 사용하여 사용자의 이메일 인증 정보를 업데이트합니다.
    5. EmailService 클래스의 send_verification_email 메서드를 호출하여 생성된 2FA 코드를 사용자의 이메일 주소로 전송합니다.
    6. 2FA 코드 전송이 성공적으로 완료되면, 성공 메시지를 포함한 응답을 반환합니다.
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
    Verify2FAView는 사용자가 제공한 2단계 인증(2FA) 코드를 검증하는 API 엔드포인트를 제공합니다.
    이 뷰는 Django REST Framework의 APIView를 상속받아 구현되었습니다.

    - permission_classes: [IsAuthenticated]를 통해 이 뷰에 접근할 수 있는 사용자를 인증된 사용자로 제한합니다. 즉, 로그인한 사용자만이 이 API를 통해 사용자 정보를 조회할 수 있습니다.
      즉, 인증되지 않은 사용자도 2FA 코드를 검증할 수 있습니다.

    POST 요청:
    이 뷰는 POST 요청을 처리하여 사용자가 제공한 2FA 코드의 유효성을 검증합니다.
    - 요청에서 'email', 'code', 그리고 'game_id' 키를 통해 전달받은 이메일 주소, 2FA 코드, 게임 ID를 사용합니다.
    - 해당 이메일 주소를 가진 사용자를 데이터베이스에서 조회합니다. 사용자가 존재하지 않는 경우, 적절한 에러 메시지와 함께 404 Not Found 응답을 반환합니다.
    - EmailService 클래스를 사용하여 제공된 2FA 코드의 유효성을 검증합니다. 코드가 유효한 경우, 게임 ID에 해당하는 게임 객체를 조회하고, player2 필드를 업데이트합니다.
    - 2FA 코드 검증이 성공적으로 완료되면, 성공 메시지를 포함한 응답을 반환합니다. 코드가 유효하지 않거나, 게임 ID에 해당하는 게임을 찾을 수 없는 경우, 적절한 에러 메시지를 반환합니다.

    이 클래스 뷰는 'verify-2fa/' URL 패턴에 연결되어 있으며, 해당 URL로 POST 요청이 들어오면 사용자의 2FA 코드를 검증하는 처리를 수행합니다.

    주요 처리 과정:
    1. POST 요청에서 'email', 'code', 'game_id' 키를 통해 전달받은 값을 사용하여 데이터베이스에서 해당 이메일 주소를 가진 사용자와 게임 ID에 해당하는 게임을 조회합니다.
    2. 해당 사용자가 존재하지 않거나, 제공된 2FA 코드가 유효하지 않은 경우, 적절한 에러 메시지와 함께 응답을 반환합니다.
    3. 게임 ID에 해당하는 게임이 존재하고, player2 필드가 비어있는 경우, player2 필드를 업데이트하고 게임 결과를 업데이트합니다.
    4. 2FA 코드 검증 및 게임 업데이트가 성공적으로 완료되면, 성공 메시지를 포함한 응답을 반환합니다.
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