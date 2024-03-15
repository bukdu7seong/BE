from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .models import Friends, FriendStatus
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from ts.exceptions import SelfRequestException, AlreadyFriendsOrRequested

AppUser = get_user_model()

class FriendRequestView(APIView):
    """
    FriendRequestView는 친구 요청을 보내는 API 엔드포인트를 제공합니다.
    사용자가 다른 사용자에게 친구 요청을 보낼 수 있습니다.
    - 인증된 사용자만이 친구 요청을 보낼 수 있습니다.
    - 요청을 받는 사용자의 ID는 요청 데이터에서 'user_id'로 전달받습니다.
    - 자기 자신에게 친구 요청을 보낼 수 없으며, 이미 친구이거나 요청을 보낸 상태라면 오류를 반환합니다.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        try:
            user_id = request.data.get('user_id')
            if user_id is None:
                return JsonResponse({'error': 'User ID is required'}, status=400)

            if request.user.id == user_id:
                raise SelfRequestException()

            friend_user = AppUser.objects.get(id=user_id)
            if Friends.objects.filter(user1=request.user, user2=friend_user).exists() or Friends.objects.filter(user1=friend_user, user2=request.user).exists():
                raise AlreadyFriendsOrRequested()

            Friends.objects.create(user1=request.user, user2=friend_user, status=FriendStatus.PENDING)
            return JsonResponse({'message': 'Friend request sent successfully'})

        except AppUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        except (SelfRequestException, AlreadyFriendsOrRequested) as e:
            return JsonResponse({'error': e.message}, status=e.status)

class FriendPendingListView(APIView):
    """
    FriendPendingListView는 대기 중인 친구 요청 목록을 조회하는 API 엔드포인트를 제공합니다.
    사용자가 받은 친구 요청 중 아직 수락되지 않은 요청의 목록을 확인할 수 있습니다.
    - 인증된 사용자만이 자신에게 온 대기 중인 친구 요청 목록을 조회할 수 있습니다.
    - 페이지네이션을 지원하여, 페이지 번호('page')와 페이지 당 항목 수('pageSize')를 쿼리 파라미터로 받습니다.
    """
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

        pending_list = [{'id': friend.user1.id, 'username': friend.user1.username, 'email': friend.user1.email, 'img': friend.user1.image.url if friend.user1.image else None} for friend in friends_page]

        return JsonResponse({
            'page': page,
            'pageSize': page_size,
            'total': paginator.count,
            'totalPages': paginator.num_pages,
            'friends': pending_list
        })

class AcceptFriendRequestView(APIView):
    """
    AcceptFriendRequestView는 친구 요청을 수락하는 API 엔드포인트를 제공합니다.
    사용자가 받은 친구 요청 중 하나를 수락할 수 있습니다.
    - 인증된 사용자만이 친구 요청을 수락할 수 있습니다.
    - 수락할 친구 요청의 ID는 요청 데이터에서 'friend_request_id'로 전달받습니다.
    - 해당 ID의 친구 요청이 존재하지 않거나 이미 수락된 경우 오류를 반환합니다.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
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
    """
    FriendAcceptedList는 친구 요청을 수락하여 현재 친구 관계에 있는 사용자 목록을 조회하는 API 엔드포인트를 제공합니다.
    사용자가 현재 친구 관계에 있는 사용자의 목록을 확인할 수 있습니다.
    - 인증된 사용자만이 자신의 친구 목록을 조회할 수 있습니다.
    - 페이지네이션을 지원하여, 페이지 번호('page')와 페이지 당 항목 수('pageSize')를 쿼리 파라미터로 받습니다.
    """
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
                'email': friend_user.email,
                'img': friend_user.image.url if friend_user.image else None
            })

        return JsonResponse({
            'page': page,
            'pageSize': page_size,
            'total': paginator.count,
            'totalPages': paginator.num_pages,
            'friends': accepted_list
        })
    
class DeleteFriendRequestView(APIView):
    """
    DeleteFriendRequestView는 친구 요청을 삭제하는 API 엔드포인트를 제공합니다.
    사용자가 보낸 친구 요청을 취소하거나 받은 친구 요청을 거절할 수 있습니다.
    - 인증된 사용자만이 친구 요청을 삭제할 수 있습니다.
    - 삭제할 친구 요청의 ID는 쿼리 파라미터 'friend_request_id'로 전달받습니다.
    - 해당 ID의 친구 요청이 존재하지 않거나 이미 수락/거절된 경우 오류를 반환합니다.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
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