from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
import json

from django.views.decorators.csrf import csrf_exempt # 삭제 예정 (테스트용) 보안 위험

from appuser.models import AppUser
from security.views import is_token_valid, get_user_id_from_token

from django.utils import timezone

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
            "image": user.image,
            "two_fact": user.two_fact,
            "nickname": user.nickname,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "language": user.language
        }
    except AppUser.DoesNotExist:
        return None

@csrf_exempt # 삭제 예정 (테스트용) 보안 위험
@require_http_methods(["GET"])
def user_profile(request):
    token = request.headers.get('Authorization', '').split(' ')[-1]

    if is_token_valid(token):
        user_id = get_user_id_from_token(token)
        user_data = get_user_info(user_id)
        if user_data:
            return JsonResponse(user_data)
        else:
            return JsonResponse({'error': 'User not found'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid token'}, status=400)
    


@csrf_exempt # 삭제 예정 (테스트용) 보안 위험
@require_http_methods(["PUT"])
def update_user_image(request):
    try:
        # 요청 헤더에서 토큰 추출
        token = request.headers.get('Authorization', '').split(' ')[-1]
        if not is_token_valid(token):
            return JsonResponse({'error': 'Invalid token'}, status=400)

        user_id = get_user_id_from_token(token)
        data = json.loads(request.body)
        new_image_url = data.get('image')

        if not new_image_url:
            return HttpResponseBadRequest("Image URL is required")

        user = AppUser.objects.get(user_id=user_id)
        user.image = new_image_url
        user.updated_at = timezone.now()
        user.save()

        return JsonResponse({'message': 'Image updated successfully'})

    except AppUser.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

@csrf_exempt # 삭제 예정 (테스트용) 보안 위험
@require_http_methods(["POST"])
def add_new_user(request):
    try:
        data = json.loads(request.body)
        new_user = AppUser(
            access_token=data.get('access_token'),
            email=data.get('email'),
            provider=data.get('provider'),
            provider_id=data.get('provider_id'),
            image=data.get('image'),
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
        print(e)
        return JsonResponse({'error': str(e)}, status=500)
    

@csrf_exempt # 삭제 예정 (테스트용) 보안 위험
@require_http_methods(["GET"])
def get_user_by_nickname(request):
    nickname = request.GET.get('nickname')

    if not nickname:
        return HttpResponseBadRequest("Nickname is required")

    try:
        user = AppUser.objects.get(nickname=nickname)
        return JsonResponse({
            "user_id": user.user_id,
            "email": user.email,
            "image": user.image,
            "nickname": user.nickname,
        })
    except AppUser.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    