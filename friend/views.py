from django.views import View
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Friends
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

AppUser = get_user_model()
from rest_framework.pagination import PageNumberPagination

class FriendPagination(PageNumberPagination):
    page_size = 5  # 페이지 당 항목 수를 설정합니다. 필요에 따라 조정하세요.
    page_size_query_param = 'pageSize'
    max_page_size = 100

class FriendView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return self.add(request)

    def get(self, request):
        if 'pending' in request.GET:
            print("pending")
            return self.pending_list(request)
        else:
            print("approved")
            return self.approved_list(request)


    def add(self, request):
        user_id = request.POST.get('user_id')
        print(request.user.id)
        print(user_id)
        try:
            logged_in_user = AppUser.objects.get(id=request.user.id)  # 수정됨
            friend_user = AppUser.objects.get(id=user_id)  # 수정됨

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

    def friends_to_json(self, friends, logged_in_user):
        friend_list = []
        for friend in friends:
            friend_info = friend.user2 if friend.user1 == logged_in_user else friend.user1
            image_url = friend_info.image.url if friend_info.image else None
            friend_list.append({
                'user_id': friend_info.id,
                'username': friend_info.username,
                'image': image_url
            })
        return friend_list

    def approved_list(self, request):
        page_size = request.GET.get('pageSize', 10)
        page = request.GET.get('page', 1)

        try:
            logged_in_user = AppUser.objects.get(id=request.user.id)
            friends = Friends.objects.filter(
                (Q(user1=logged_in_user) | Q(user2=logged_in_user)) & Q(status='ACCEPTED')
            )

            paginator = Paginator(friends, page_size)
            friends_page = paginator.get_page(page)

            friend_list = []
            for friend in friends_page:
                friend_info = friend.user2 if friend.user1 == logged_in_user else friend.user1
                image_url = friend_info.image.url if friend_info.image else None  # 이미지가 있으면 URL을 가져오고, 없으면 None
                friend_list.append({
                    'user_id': friend_info.id,
                    'username': friend_info.username,
                    'image': image_url
                })

            return JsonResponse({'friends': friend_list})

        except AppUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

    def pending_list(self, request):
        page_size = request.GET.get('pageSize', 10)
        page = request.GET.get('page', 1)

        try:
            logged_in_user = AppUser.objects.get(id=request.user.id)
            friends = Friends.objects.filter(user2=logged_in_user, status='PENDING').order_by('id')

            paginator = Paginator(friends, page_size)
            friends_page = paginator.get_page(page)

            friend_list = []
            for friend in friends_page:
                friend_info = friend.user2 if friend.user1 == logged_in_user else friend.user1
                image_url = friend_info.image.url if friend_info.image else None  # 이미지가 있으면 URL을 가져오고, 없으면 None
                friend_list.append({
                    'user_id': friend_info.id,
                    'username': friend_info.username,
                    'image': image_url
                })
            return JsonResponse({'friends': friend_list})

        except AppUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)


class DenyFriendView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        try:
            logged_in_user = AppUser.objects.get(id=request.user.id)
            friend_user = AppUser.objects.get(id=user_id)

            friend_request = Friends.objects.get(user1=friend_user, user2=logged_in_user, status='PENDING')
            friend_request.delete()

            return JsonResponse({'message': 'Friend request denied'})

        except AppUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        except Friends.DoesNotExist:
            return JsonResponse({'error': 'Friend request not found'}, status=404)

class ApproveFriendView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        try:
            logged_in_user = AppUser.objects.get(id=request.user.id)
            friend_user = AppUser.objects.get(id=user_id)
            print("login user : ", logged_in_user)
            print("friend user : ", friend_user)
            friend_request = Friends.objects.get(user1=friend_user, user2=logged_in_user, status='PENDING')
            friend_request.status = 'APPROVED'
            friend_request.save()

            return JsonResponse({'message': 'Friend request approved'})

        except AppUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        except Friends.DoesNotExist:
            return JsonResponse({'error': 'Friend request not found'}, status=404)