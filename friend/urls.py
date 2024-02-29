from django.urls import path
from .views import FriendRequestView, FriendPendingListView, AcceptFriendRequestView, FriendAcceptedList, DeleteFriendRequestView

urlpatterns = [
    path('send-friend-request/', FriendRequestView.as_view(), name='send-friend-request'),
    path('pending-friends/', FriendPendingListView.as_view(), name='pending-friends-list'),
    path('accept-friend-request/', AcceptFriendRequestView.as_view(), name='accept-friend-request'),
    path('accepted-friends/', FriendAcceptedList.as_view(), name='accepted-friends-list'),
    path('delete-friend-request/', DeleteFriendRequestView.as_view(), name='delete-friend-request'),
]