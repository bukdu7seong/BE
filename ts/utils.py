from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework import status
from django.http import JsonResponse
from rest_framework.serializers import ValidationError
from django.contrib.auth import get_user_model
from . import exceptions

User = get_user_model()

def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if isinstance(exc, ValidationError):
        return JsonResponse({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    elif isinstance(exc, User.DoesNotExist):
        return JsonResponse({'error': str(exc)}, status=status.HTTP_404_NOT_FOUND)
    elif isinstance(exc, exceptions.TwoFactorException) or isinstance(exc, exceptions.FTOauthException):
        return JsonResponse({'error': str(exc)}, status=exc.status)
    # 여기에 추가적인 커스텀 예외 처리 로직을 통합
    # friends
    elif isinstance(exc, exceptions.SelfRequestException) or isinstance(exc, exceptions.AlreadyFriendsOrRequested):
        return JsonResponse({'error': exc.message}, status=exc.status or 400)
    # game
    elif isinstance(exc, exceptions.InvalidGameModeException) or isinstance(exc, exceptions.PlayerNotMatchedException):
        return JsonResponse({'error': exc.message}, status=exc.status or 400)
    return response
