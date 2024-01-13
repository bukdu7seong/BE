from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods

import json

from django.views.decorators.csrf import csrf_exempt # 삭제 예정 (테스트용) 보안 위험

from friends.models import Friends
from appuser.models import AppUser
from security.views import is_token_valid, get_user_id_from_token


@csrf_exempt # 삭제 예정 (테스트용) 보안 위험
@require_http_methods(["POST"])
def add_friend(request):
    # 요청 헤더에서 토큰 추출
    token = request.headers.get('Authorization', '').split(' ')[-1]
    
    if not is_token_valid(token):
        return JsonResponse({'error': 'Invalid token'}, status=400)

    logged_in_user_id = get_user_id_from_token(token)
    friend_id = request.GET.get('nickname')

    if not friend_id:
        return JsonResponse({'error': 'Nickname is required'}, status=400)

    try:
        logged_in_user = AppUser.objects.get(user_id=logged_in_user_id)
        friend_user = AppUser.objects.get(user_id=friend_id)

        if Friends.objects.filter(user1=logged_in_user, user2=friend_user).exists():
            return JsonResponse({'error': 'Friend request already exists'}, status=400)

        new_friend = Friends.objects.create(
            user1=logged_in_user,
            user2=friend_user,
            status='PENDING'
        )

        new_friend.save()

        return JsonResponse({'message': 'Friend request sent'})

    except AppUser.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
@csrf_exempt # 삭제 예정 (테스트용) 보안 위험
@require_http_methods(["GET"])
def get_friend_pending_list(request):
    # 요청 헤더에서 토큰 추출
    token = request.headers.get('Authorization', '').split(' ')[-1]
    
    if not is_token_valid(token):
        return JsonResponse({'error': 'Invalid token'}, status=400)

    logged_in_user_id = get_user_id_from_token(token)

    try:
        logged_in_user = AppUser.objects.get(user_id=logged_in_user_id)
        friends = Friends.objects.filter(user2=logged_in_user, status='PENDING')
        friend_list = []
        for friend in friends:
            friend_list.append({
                'user_id': friend.user1.user_id,
                'nickname': friend.user1.nickname,
                'image': friend.user1.image
            })
        return JsonResponse({'friends': friend_list})

    except AppUser.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
@csrf_exempt # 삭제 예정 (테스트용) 보안 위험
@require_http_methods(["POST"])
def approve_friend_request(request):
    # 요청 헤더에서 토큰 추출
    token = request.headers.get('Authorization', '').split(' ')[-1]
    
    if not is_token_valid(token):
        return JsonResponse({'error': 'Invalid token'}, status=400)

    logged_in_user_id = get_user_id_from_token(token)
    friend_id = request.GET.get('friendUserId')

    if not friend_id:
        return JsonResponse({'error': 'Nickname is required'}, status=400)

    try:
        logged_in_user = AppUser.objects.get(user_id=logged_in_user_id)
        friend_user = AppUser.objects.get(user_id=friend_id)

        friend_request = Friends.objects.get(user1=friend_user, user2=logged_in_user)
        friend_request.status = 'APPROVED'
        friend_request.save()

        return JsonResponse({'message': 'Friend request approved'})

    except AppUser.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Friends.DoesNotExist:
        return JsonResponse({'error': 'Friend request not found'}, status=404)