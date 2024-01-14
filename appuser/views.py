from django.http import JsonResponse, HttpResponseBadRequest
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from appuser.models import AppUser
from security.views import is_token_valid, get_user_id_from_token, get_token_from_request
from django.utils import timezone
import json

from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
import base64
import logging

logger = logging.getLogger(__name__)
@csrf_exempt # 삭제 예정 (테스트용) 보안 위험
@require_http_methods(["GET"])
def login(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION')

    if auth_header is None:
        return JsonResponse({'error': 'Authorization header is required'}, status=400)

    token_type, token = auth_header.split()

    if token_type != 'Bearer':
        return JsonResponse({'error': 'Invalid token type. Expected "Bearer"'}, status=400)

    if is_token_valid(token):
        user_id = get_user_id_from_token(token)
        if AppUser.objects.filter(user_id=user_id).exists():
            return JsonResponse({'message': 'Token verified successfully'})
        else:
            return JsonResponse({'error': 'User does not exist'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid token'}, status=400)
    
@method_decorator(csrf_exempt, name='dispatch') # 삭제 예정 (테스트용) 보안 위험
class ProfileView(View):
        # 사용자 정보 조회 함수
    def get_user_info(user_id):
        try:
            user = AppUser.objects.get(user_id=user_id)
            return {
                "user_id": user.user_id,
                "access_token": user.access_token,
                "email": user.email,
                "provider": user.provider,
                "provider_id": user.provider_id,
                "image": user.image,  # Return the image data as a string
                "two_fact": user.two_fact,
                "nickname": user.nickname,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "language": user.language
            }
        except AppUser.DoesNotExist:
            return None

    
    def dispatch(self, request, *args, **kwargs):
        token = get_token_from_request(request)

        if not is_token_valid(token):
            return JsonResponse({'error': 'Invalid token'}, status=400)

        self.user_id = get_user_id_from_token(token)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        user_data = ProfileView.get_user_info(self.user_id)
        if user_data:
            return JsonResponse(user_data)
        else:
            return JsonResponse({'error': 'User not found'}, status=404)

    def patch(self, request, *args, **kwargs):
        data = json.loads(request.body)
        new_user_nickname = data.get('nickname')
        new_image_base64 = data.get('image')

        try:
            user = AppUser.objects.get(user_id=self.user_id)

            if new_user_nickname:
                user.nickname = new_user_nickname
            elif new_image_base64:
                user.image = new_image_base64  # Save the Base64 string directly
            else:
                return HttpResponseBadRequest("Invalid JSON")

            user.updated_at = timezone.now()
            user.save()

            return JsonResponse({'message': 'Image updated successfully'})

        except AppUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        except AppUser.MultipleObjectsReturned:
            return JsonResponse({'error': 'Multiple users found with the same user_id'}, status=500)
        
    def delete(self, request, *args, **kwargs):
        user = AppUser.objects.get(user_id=self.user_id)
        user.delete()

        return JsonResponse({'message': 'User deleted successfully'})

@method_decorator(csrf_exempt, name='dispatch') # 삭제 예정 (테스트용) 보안 위험
class UserView(View):
    def get(self, request, user_id=None, *args, **kwargs):
        nickname = request.GET.get('nickname')

        try:
            if user_id:
                user = get_object_or_404(AppUser, user_id=user_id)
            elif nickname:
                user = get_object_or_404(AppUser, nickname=nickname)
            else:
                return HttpResponseBadRequest("Either user_id or nickname is required")

            return JsonResponse({
                "user_id": user.user_id,
                "email": user.email,
                "image": user.image,
                "nickname": user.nickname,
            })
        except AppUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
    
@csrf_exempt # 삭제 예정 (테스트용) 보안 위험
@require_http_methods(["POST"])
def add_new_user(request):
    try:
        data = json.loads(request.body)
        new_user = AppUser(
            access_token=data.get('access_token'),
            email=data.get('email'),
            provider=data.get('provider', 'google'),
            provider_id=data.get('provider_id', 'google'),
            image=data.get('image'),  # Save the image data as a string
            two_fact=data.get('two_fact', False),
            nickname=data.get('nickname'),
            created_at=data.get('created_at', timezone.now()),
            updated_at=data.get('updated_at', timezone.now()),
            language=data.get('language', 'KO')
        )
        new_user.save()
        return JsonResponse({'message': 'User added successfully'})
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")
    except Exception as e:
        logger.exception("Unexpected error in add_new_user")
        return JsonResponse({'error': f'Unexpected error: {str(e)}'}, status=500)
