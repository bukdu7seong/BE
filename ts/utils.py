from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework import status
from django.http import JsonResponse
from rest_framework.serializers import ValidationError
from django.contrib.auth import get_user_model
from . import exceptions

User = get_user_model()


def custom_exception_handler(exc, context):
    # DRF의 기본 예외 처리 호출
    response = drf_exception_handler(exc, context)

    # 여기에서 커스텀 예외 처리 로직을 추가
    if isinstance(exc, ValidationError):
        return JsonResponse({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    elif isinstance(exc, User.DoesNotExist):
        return JsonResponse({'error': str(exc)}, status=status.HTTP_404_NOT_FOUND)
    elif isinstance(exc, exceptions.TwoFactorException):
        return JsonResponse({'error': str(exc)}, status=exc.status)
    elif isinstance(exc, exceptions.FTOauthException):
        return JsonResponse({'error': str(exc)}, status=exc.status)
    return response
