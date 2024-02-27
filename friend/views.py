from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .models import Friends, FriendStatus
from django.core.paginator import Paginator
from django.db.models import Q

AppUser = get_user_model()

class FriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user_id = request.data.get('user_id')
            if user_id is None:
                return JsonResponse({'error': 'User ID is required'}, status=400)

            if request.user.id == user_id:
                return JsonResponse({'error': 'You cannot send a friend request to yourself'}, status=400)

            friend_user = AppUser.objects.get(id=user_id)
            if Friends.objects.filter(user1=request.user, user2=friend_user).exists() or Friends.objects.filter(user1=friend_user, user2=request.user).exists():
                return JsonResponse({'error': 'Friend request already sent or you are already friends'}, status=400)

            Friends.objects.create(user1=request.user, user2=friend_user, status=FriendStatus.PENDING)
            return JsonResponse({'message': 'Friend request sent successfully'})

        except AppUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

class FriendPendingListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('pageSize', 10)
        try:
            page = int(page)
            page_size = int(page_size)
        except ValueError:
            return JsonResponse({'error': 'Invalid page or pageSize'}, status=400)

        pending_friends = Friends.objects.filter(user2=request.user, status=FriendStatus.PENDING).order_by('id')
        paginator = Paginator(pending_friends, page_size)

        try:
            friends_page = paginator.page(page)
        except:
            return JsonResponse({'error': 'Page not found'}, status=404)

        pending_list = [{'id': friend.user1.id, 'username': friend.user1.username, 'email': friend.user1.email} for friend in friends_page]

        return JsonResponse({
            'page': page,
            'pageSize': page_size,
            'total': paginator.count,
            'totalPages': paginator.num_pages,
            'friends': pending_list
        })

class AcceptFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        friend_request_id = request.data.get('friend_request_id')
        if not friend_request_id:
            return JsonResponse({'error': 'Friend request ID is required'}, status=400)

        try:
            friend_request = Friends.objects.get(
                Q(user1=request.user, id=friend_request_id) | Q(user2=request.user, id=friend_request_id),
                status=FriendStatus.PENDING
            )
        except Friends.DoesNotExist:
            return JsonResponse({'error': 'Friend request not found or already accepted'}, status=404)

        friend_request.status = FriendStatus.ACCEPTED
        friend_request.save()

        return JsonResponse({'message': 'Friend request accepted successfully'})
    
class FriendAcceptedList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('pageSize', 10)
        try:
            page = int(page)
            page_size = int(page_size)
        except ValueError:
            return JsonResponse({'error': 'Invalid page or pageSize'}, status=400)

        accepted_friends = Friends.objects.filter(
            Q(user1=request.user, status=FriendStatus.ACCEPTED) | 
            Q(user2=request.user, status=FriendStatus.ACCEPTED)
        ).distinct().order_by('id')

        paginator = Paginator(accepted_friends, page_size)

        try:
            friends_page = paginator.page(page)
        except:
            return JsonResponse({'error': 'Page not found'}, status=404)

        accepted_list = []
        for friend in friends_page:
            friend_user = friend.user2 if friend.user1 == request.user else friend.user1
            accepted_list.append({
                'id': friend_user.id, 
                'username': friend_user.username, 
                'email': friend_user.email
            })

        return JsonResponse({
            'page': page,
            'pageSize': page_size,
            'total': paginator.count,
            'totalPages': paginator.num_pages,
            'friends': accepted_list
        })
    
class DeleteFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        friend_request_id = request.query_params.get('friend_request_id')
        if not friend_request_id:
            return JsonResponse({'error': 'Friend request ID is required'}, status=400)

        try:
            friend_request = Friends.objects.get(
                Q(user1=request.user, id=friend_request_id, status=FriendStatus.PENDING) |
                Q(user2=request.user, id=friend_request_id, status=FriendStatus.PENDING)
            )
            friend_request.delete()
            return JsonResponse({'message': 'Friend request deleted successfully'})
        except Friends.DoesNotExist:
            return JsonResponse({'error': 'Friend request not found or not in pending status'}, status=404)