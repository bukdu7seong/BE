from django.views import View
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Friends
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

AppUser = get_user_model()

class FriendView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return self.add(request)

    def get(self, request):
        if 'pending' in request.GET:
            return self.pending_list(request)
        else:
            return self.approved_list(request)


    def add(self, request):
        user_id = request.POST.get('user_id')
        try:
            logged_in_user = AppUser.objects.get(user_id=request.user_id)
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

    def approved_list(self, request):
        page_size = request.GET.get('pageSize', 10)
        page = request.GET.get('page', 1)

        try:
            logged_in_user = AppUser.objects.get(user_id=request.user_id)
            friends = Friends.objects.filter(
                (Q(user1=logged_in_user) | Q(user2=logged_in_user)) & Q(status='ACCEPTED')
            )

            paginator = Paginator(friends, page_size)
            friends_page = paginator.get_page(page)

            friend_list = []
            for friend in friends_page:
                friend_info = friend.user2 if friend.user1 == logged_in_user else friend.user1
                friend_list.append({
                    'user_id': friend_info.user_id,
                    'nickname': friend_info.nickname,
                    'image': friend_info.image
                })

            return JsonResponse({'friends': friend_list})

        except AppUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

    def pending_list(self, request):
        page_size = request.GET.get('pageSize', 10)
        page = request.GET.get('page', 1)

        try:
            logged_in_user = AppUser.objects.get(user_id=request.user_id)
            friends = Friends.objects.filter(user2=logged_in_user, status='PENDING').order_by('id')

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


class DenyFriendView(View):
    def post(self, request, user_id):
        logged_in_user_id = '1' # 인증과정 구현 이후에 메소드를 호출하여 로그인한 사용자의 user_id를 가져옵니다.
        return self.deny(request, logged_in_user_id, user_id)

    def deny(self, request, logged_in_user_id, user_id):
        try:
            logged_in_user = AppUser.objects.get(user_id=logged_in_user_id)
            friend_user = AppUser.objects.get(user_id=user_id)

            friend_request = Friends.objects.get(user1=friend_user, user2=logged_in_user, status='PENDING')
            friend_request.delete()

            return JsonResponse({'message': 'Friend request denied'})

        except AppUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        except Friends.DoesNotExist:
            return JsonResponse({'error': 'Friend request not found'}, status=404)


class ApproveFriendView(View):
    def post(self, request, user_id):
        logged_in_user_id = '1' # 인증과정 구현 이후에 메소드를 호출하여 로그인한 사용자의 user_id를 가져옵니다. 
        return self.approve(request, logged_in_user_id, user_id)

    def approve(self, request, logged_in_user_id, user_id):
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