from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
import json

from django.views.decorators.csrf import csrf_exempt # 삭제 예정 (테스트용) 보안 위험

from user.models import AppUser

# 토큰 유효성 검사 함수
def is_token_valid(token):
    return token.startswith('mockToken_')

# 토큰에서 user_id 추출 함수
def get_user_id_from_token(token):
    return token.replace('mockToken_', '')


@csrf_exempt # 삭제 예정 (테스트용) 보안 위험
@require_http_methods(["POST"])
def verify_token(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        token = data.get('token')

        if is_token_valid(token):
            user_id = get_user_id_from_token(token)
            if AppUser.objects.filter(user_id=user_id).exists():
                return JsonResponse({'message': 'Token verified successfully'})
            else:
                return JsonResponse({'error': 'User does not exist'}, status=404)
        else:
            return JsonResponse({'error': 'Invalid token'}, status=400)