from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
import json

from django.views.decorators.csrf import csrf_exempt # 삭제 예정 (테스트용) 보안 위험

from appuser.models import AppUser

# 토큰 유효성 검사 함수
def is_token_valid(token):
    return token.startswith('mockToken_')

# 토큰에서 user_id 추출 함수
def get_user_id_from_token(token):
    return token.replace('mockToken_', '')

def get_token_from_request(request):
    return request.headers.get('Authorization', '').split(' ')[-1]
