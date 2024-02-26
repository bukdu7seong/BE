from django.http import JsonResponse
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

class CustomExceptionHandlerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if isinstance(exception, ValueError):
            # ValueError 예외를 처리하고, custom JSON response 반환
            return JsonResponse({'error': str(exception)}, status=400)
        elif isinstance(exception, PermissionError):
            # PermissionError 예외를 처리하고, custom JSON response 반환
            return JsonResponse({'error': str(exception)}, status=403)
        elif isinstance(exception, IntegrityError):
            return JsonResponse({'error': str(exception)}, status=409)
        elif isinstance(exception, ObjectDoesNotExist):
            return JsonResponse({'error': str(exception)}, status=404)
        return None
