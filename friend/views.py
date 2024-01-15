from django.views import View
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.core.paginator import Paginator
from friend.models import Friends
from user.models import AppUser
from security.views import is_token_valid, get_user_id_from_token

class FriendView(View):
    @method_decorator(csrf_exempt) # 삭제 예정 (테스트용) 보안 위험
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, user_id=None):
        logged_in_user_id = self._get_logged_in_user_id(request)
        if not logged_in_user_id:
            return JsonResponse({'error': 'Invalid token'}, status=400)

        if user_id:
            return self.approve_friend_request(request, logged_in_user_id, user_id)
        else:
            return self.add_friend(request, logged_in_user_id)

    def get(self, request):
        logged_in_user_id = self._get_logged_in_user_id(request)
        if not logged_in_user_id:
            return JsonResponse({'error': 'Invalid token'}, status=400)

        return self.get_friend_pending_list(request, logged_in_user_id)

    def _get_token(self, request):
        return request.headers.get('Authorization', '').split(' ')[-1]

    def _get_logged_in_user_id(self, request):
        token = self._get_token(request)
        if is_token_valid(token):
            return get_user_id_from_token(token)
        else:
            return None

    @method_decorator(csrf_exempt) # 삭제 예정 (테스트용) 보안 위험
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, user_id=None):
        logged_in_user_id = self._get_logged_in_user_id(request)
        if not logged_in_user_id:
            return JsonResponse({'error': 'Invalid token'}, status=400)

        if user_id:
            return self.approve_friend_request(request, logged_in_user_id, user_id)
        else:
            return self.add_friend(request, logged_in_user_id)

    def get(self, request):
        logged_in_user_id = self._get_logged_in_user_id(request)
        if not logged_in_user_id:
            return JsonResponse({'error': 'Invalid token'}, status=400)

        return self.get_friend_pending_list(request, logged_in_user_id)

    def _get_token(self, request):
        return request.headers.get('Authorization', '').split(' ')[-1]

    def _get_logged_in_user_id(self, request):
        token = self._get_token(request)
        if is_token_valid(token):
            return get_user_id_from_token(token)
        else:
            return None
        
    @method_decorator(csrf_exempt) # 삭제 예정 (테스트용) 보안 위험
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, user_id=None):
        logged_in_user_id = self._get_logged_in_user_id(request)
        if not logged_in_user_id:
            return JsonResponse({'error': 'Invalid token'}, status=400)

        if user_id:
            return self.approve_friend_request(request, logged_in_user_id, user_id)
        else:
            return self.add_friend(request, logged_in_user_id)

    def get(self, request):
        logged_in_user_id = self._get_logged_in_user_id(request)
        if not logged_in_user_id:
            return JsonResponse({'error': 'Invalid token'}, status=400)

        return self.get_friend_pending_list(request, logged_in_user_id)

    def _get_token(self, request):
        return request.headers.get('Authorization', '').split(' ')[-1]

    def _get_logged_in_user_id(self, request):
        token = self._get_token(request)
        if is_token_valid(token):
            return get_user_id_from_token(token)
        else:
            return None

    def add_friend(self, request, logged_in_user_id):
        user_id = request.POST.get('user_id')
        try:
            logged_in_user = AppUser.objects.get(user_id=logged_in_user_id)
            friend_user = AppUser.objects.get(user_id=user_id)

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

    def get_friend_pending_list(self, request, logged_in_user_id):
        page_size = request.GET.get('pageSize', 10)
        page = request.GET.get('page', 1)

        try:
            logged_in_user = AppUser.objects.get(user_id=logged_in_user_id)
            friends = Friends.objects.filter(user2=logged_in_user, status='PENDING')

            paginator = Paginator(friends, page_size)
            friends_page = paginator.get_page(page)

            friend_list = []
            for friend in friends_page:
                friend_list.append({
                    'user_id': friend.user1.user_id,
                    'nickname': friend.user1.nickname,
                    'image': friend.user1.image
                })
            return JsonResponse({'friends': friend_list})

        except AppUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

    def approve_friend_request(self, request, logged_in_user_id, user_id):
        try:
            logged_in_user = AppUser.objects.get(user_id=logged_in_user_id)
            friend_user = AppUser.objects.get(user_id=user_id)

            friend_request = Friends.objects.get(user1=friend_user, user2=logged_in_user, status='PENDING')
            friend_request.status = 'APPROVED'
            friend_request.save()

            return JsonResponse({'message': 'Friend request approved'})

        except AppUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        except Friends.DoesNotExist:
            return JsonResponse({'error': 'Friend request not found'}, status=404)