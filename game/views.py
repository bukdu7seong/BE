from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
import json
from django.views.decorators.csrf import csrf_exempt # 삭제 예정 (테스트용) 보안 위험