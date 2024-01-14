from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods

import json

from django.views.decorators.csrf import csrf_exempt # 삭제 예정 (테스트용) 보안 위험

from friends.models import Friends
from appuser.models import AppUser
from security.views import is_token_valid, get_user_id_from_token, get_token_from_request


from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage

@method_decorator(csrf_exempt, name='dispatch')
class FriendView(View):
    # 중복된 페이지네이션 로직을 별도의 메소드로 분리
    def paginate_queryset(self, queryset, page_size, page):
        paginator = Paginator(queryset, page_size)
        try:
            return paginator.page(page)
        except EmptyPage:
            return None  # 페이지가 없으면 None 반환

    # 중복된 JSON 변환 로직을 별도의 메소드로 분리
    def get_paginated_response(self, paginated_page, page, page_size, response_key):
        if paginated_page is None:
            return JsonResponse({'error': 'No more pages'}, status=404)

        object_list = [
            {
                'user_id': obj.user2.id if obj.user1.id == self.current_user_id else obj.user1.id,
                'nickname': obj.user2.nickname if obj.user1.id == self.current_user_id else obj.user1.nickname,
                'image': obj.user2.image.url if obj.user1.id == self.current_user_id else obj.user1.image.url,
            }
            for obj in paginated_page
        ]

        return JsonResponse({
            'page': page,
            'pageSize': page_size,
            response_key: object_list,
            'totalPages': paginated_page.paginator.num_pages,
            'totalObjects': paginated_page.paginator.count
        })

    def get_friend_list(self, request):
        # 페이지네이션 파라미터
        page_size = request.GET.get('pageSize', 5)
        page = request.GET.get('page', 1)
        
        # 현재 사용자의 친구 목록 조회 로직 구현
        self.current_user_id = get_user_id_from_token(get_token_from_request(request))
        friends_queryset = Friends.objects.filter(
            (Q(user1_id=self.current_user_id) | Q(user2_id=self.current_user_id)) & Q(status='APPROVED')
        ).distinct()

        friends_page = self.paginate_queryset(friends_queryset, page_size, page)
        return self.get_paginated_response(friends_page, page, page_size, 'friends')

    def get_friend_requests(self, request):
        # 페이지네이션 파라미터
        page_size = request.GET.get('pageSize', 5)
        page = request.GET.get('page', 1)
        
        # 현재 사용자의 친구 요청 목록 조회 로직 구현
        self.current_user_id = get_user_id_from_token(get_token_from_request(request))
        friend_requests_queryset = Friends.objects.filter(
            user2_id=self.current_user_id,
            status='PENDING'
        )

        friend_requests_page = self.paginate_queryset(friend_requests_queryset, page_size, page)
        return self.get_paginated_response(friend_requests_page, page, page_size, 'friendRequests')
    # 중복된 사용자 ID 가져오는 로직을 별도의 메소드로 분리
    def get_current_user_id(self, request):
        return get_user_id_from_token(get_token_from_request(request))

    # 중복된 친구 요청 객체 가져오는 로직을 별도의 메소드로 분리
    def get_friend_request(self, user1_id, user2_id):
        try:
            return Friends.objects.get(user1_id=user1_id, user2_id=user2_id)
        except Friends.DoesNotExist:
            return None

    def accept_friend_request(self, request, user_id):
        # 친구 요청 수락 로직 구현
        current_user_id = self.get_current_user_id(request)
        friend_request = self.get_friend_request(user_id, current_user_id)
        if friend_request is None:
            return JsonResponse({'error': 'Friend request not found'}, status=404)

        friend_request.status = 'APPROVED'
        friend_request.save()
        return JsonResponse({'message': 'Friend request approved'})

    def deny_friend_request(self, request, user_id):
        # 친구 요청 거절 로직 구현
        current_user_id = self.get_current_user_id(request)
        friend_request = self.get_friend_request(user_id, current_user_id)
        if friend_request is None:
            return JsonResponse({'error': 'Friend request not found'}, status=404)

        friend_request.delete()
        return JsonResponse({'message': 'Friend request denied'})

    def request_friend(self, request, user_id):
        # 친구 요청 로직 구현
        current_user_id = self.get_current_user_id(request)
        friend_request = self.get_friend_request(current_user_id, user_id)
        if friend_request is None:
            return JsonResponse({'error': 'Friend request not found'}, status=404)

        friend_request.status = 'PENDING'
        friend_request.save()
        return JsonResponse({'message': 'Friend request sent'})

    def post(self, request, user_id=None, *args, **kwargs):
        if 'accept' in request.path:
            # 친구 요청 수락 로직 구현
            return self.accept_friend_request(request, user_id)
        elif 'deny' in request.path:
            # 친구 요청 거절 로직 구현
            return self.deny_friend_request(request, user_id)
        elif 'request' in request.path:
            # 친구 요청 로직 구현
            return self.request_friend(request, user_id)
        else:
            return HttpResponseBadRequest('Invalid action')

    def get(self, request, *args, **kwargs):
        if 'request' in request.path:
            return self.get_friend_requests(request)
        else:
            return self.get_friend_list(request)




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